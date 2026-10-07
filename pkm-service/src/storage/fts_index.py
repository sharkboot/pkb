"""SQLite FTS5 full-text search index — zero external dependencies.

Uses Python standard library sqlite3 with FTS5 virtual table.
Index file lives at knowledge_base/fts_index.db.
"""
import os
import sqlite3
import logging
from typing import List, Optional, Dict, Any

from models.schemas import KnowledgeUnit
from core.config import settings

logger = logging.getLogger(__name__)

_DB_FILENAME = "fts_index.db"
_ACTIVE_STATUSES = ("draft", "active")


def _escape_fts_keyword(raw: str) -> str:
    """Sanitize user input for safe use in an FTS5 double-quoted phrase."""
    return raw.replace('"', "").strip()


class FTSIndex:
    """SQLite FTS5 full-text search index for knowledge items.

    Tables:
        fts_content: FTS5 virtual table (title, summary, body, tags, category)
        fts_meta:    regular table for id → status mapping
    """

    def __init__(self):
        self.db_path = os.path.join(settings.knowledge_base_path, _DB_FILENAME)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_schema(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS fts_content USING fts5(
                    title,
                    summary,
                    body,
                    tags,
                    category
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fts_meta (
                    id       TEXT PRIMARY KEY,
                    status   TEXT DEFAULT 'draft',
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_meta_status ON fts_meta(status)")
            logger.info(f"FTS5 index ready at {self.db_path}")

    # ========== Write operations ==========

    def upsert(self, knowledge: KnowledgeUnit) -> None:
        """Insert or update a knowledge item in the FTS index."""
        with self._connect() as conn:
            conn.execute("DELETE FROM fts_content WHERE rowid = ?", [str(knowledge.id)])
            conn.execute(
                """
                INSERT INTO fts_content (rowid, title, summary, body, tags, category)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    str(knowledge.id),
                    knowledge.title or "",
                    knowledge.summary or "",
                    knowledge.content or "",
                    " ".join(knowledge.tags or []),
                    knowledge.category or "",
                ],
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO fts_meta (id, status, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                [
                    str(knowledge.id),
                    knowledge.status.value if knowledge.status else "draft",
                    knowledge.created_at.isoformat() if knowledge.created_at else None,
                    knowledge.updated_at.isoformat() if knowledge.updated_at else None,
                ],
            )

    def delete(self, knowledge_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM fts_content WHERE rowid = ?", [knowledge_id])
            conn.execute("DELETE FROM fts_meta WHERE id = ?", [knowledge_id])

    def delete_by_status(self, status: str) -> int:
        with self._connect() as conn:
            rows = conn.execute("SELECT id FROM fts_meta WHERE status = ?", [status]).fetchall()
            ids = [r[0] for r in rows]
            if ids:
                placeholders = ",".join("?" * len(ids))
                conn.execute(f"DELETE FROM fts_content WHERE rowid IN ({placeholders})", ids)
                conn.execute(f"DELETE FROM fts_meta WHERE id IN ({placeholders})", ids)
            return len(ids)

    # ========== Search ==========

    def search(
        self,
        keyword: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """FTS5 full-text search.

        Args:
            keyword: search phrase (matched against title/summary/body/tags/category)
            category: optional category filter
            tags: optional list of tags that must all be present
            limit: max results

        Returns:
            List of {id, title, bm25_score, status} sorted by relevance.
            Falls back to LIKE search if FTS5 MATCH fails on unusual input.
        """
        safe_kw = _escape_fts_keyword(keyword)
        if not safe_kw:
            return []

        # Build FTS5 match phrase: search across all columns with a quoted phrase
        # FTS5 OR across columns so keyword in any column matches
        all_cols = ("title", "summary", "body", "tags", "category")
        fts_phrase = f'"{safe_kw}"'
        # Use OR to search across columns
        match_expr = " OR ".join(f"{col} : {fts_phrase}" for col in all_cols)

        sql = (
            "SELECT rowid AS id, title, "
            "bm25(fts_content, 1.0, 0.5, 1.5, 0.3, 0.2) AS score "
            "FROM fts_content "
            f"WHERE fts_content MATCH ({match_expr})"
        )
        params: List[str] = []  # FTS5 phrases are inlined; no bind params for MATCH

        if tags:
            for tag in tags:
                safe_tag = _escape_fts_keyword(tag)
                sql += f" AND tags : \"{safe_tag}\""

        if category:
            safe_cat = _escape_fts_keyword(category)
            sql += f" AND category = \"{safe_cat}\""

        sql += " AND rowid IN (SELECT id FROM fts_meta WHERE status IN (?, ?))"
        params.extend(_ACTIVE_STATUSES)

        sql += " ORDER BY score ASC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            try:
                rows = conn.execute(sql, params).fetchall()
            except sqlite3.OperationalError as e:
                logger.debug(f"FTS5 MATCH error ({e}); falling back to LIKE search")
                return self._fallback_like_search(keyword, tags, category, limit)

        results = []
        with self._connect() as conn:
            for row in rows:
                rid, title, raw_score = row
                meta = conn.execute("SELECT status FROM fts_meta WHERE id = ?", [rid]).fetchone()
                # bm25: lower = better match; negate for "higher is better"
                results.append({
                    "id": rid,
                    "title": title,
                    "bm25_score": -raw_score if raw_score else 0.0,
                    "status": meta[0] if meta else "draft",
                })
        return results

    def _fallback_like_search(
        self,
        keyword: str,
        tags: Optional[List[str]],
        category: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """LIKE-based fallback for cases where FTS5 MATCH syntax is problematic."""
        like_pattern = f"%{keyword}%"
        sql = """
            SELECT rowid AS id, title
            FROM fts_content
            WHERE (title LIKE ? OR summary LIKE ? OR body LIKE ?)
        """
        params: List[str] = [like_pattern, like_pattern, like_pattern]

        if category:
            sql += " AND category = ?"
            params.append(category)

        sql += " AND rowid IN (SELECT id FROM fts_meta WHERE status IN (?, ?))"
        params.extend(_ACTIVE_STATUSES)

        sql += " LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        return [
            {"id": r[0], "title": r[1], "bm25_score": 0.0, "status": "draft"}
            for r in rows
        ]

    def count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM fts_meta").fetchone()[0]

    def rebuild(self, all_knowledge: List[KnowledgeUnit]) -> int:
        """Rebuild FTS index from a list of knowledge items."""
        with self._connect() as conn:
            conn.execute("DELETE FROM fts_content")
            conn.execute("DELETE FROM fts_meta")
        for k in all_knowledge:
            self.upsert(k)
        logger.info(f"FTS index rebuilt: {len(all_knowledge)} entries")
        return len(all_knowledge)


# Singleton
fts_index = FTSIndex()
