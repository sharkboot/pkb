"""Vector storage abstraction — Chroma (local, zero-config) with graceful degradation.

Usage:
    from storage.vector_storage import VectorStorage
    vs = VectorStorage()
    await vs.upsert_knowledge(knowledge, embedding)
    results = await vs.semantic_search(query_embedding, limit=10)
    if vs.enabled: ...  # falls back to catalog search when disabled
"""
import asyncio
import logging
from typing import List, Optional, Tuple, Dict, Any

from uuid import UUID
from models.schemas import KnowledgeUnit
from core.config import settings

logger = logging.getLogger(__name__)


class VectorStorage:
    """Chroma-backed vector storage.

    - Local persistent Chroma instance (no external service needed)
    - Each knowledge item is stored with its content embedding + metadata
    - When vector_store_enabled is False, all operations are no-ops and
      the caller should fall back to keyword/catalog search
    """

    def __init__(self):
        self._client = None
        self._collection = None
        self.enabled = settings.vector_store_enabled
        self._lock = asyncio.Lock()
        if self.enabled:
            self._init_chroma()

    def _init_chroma(self):
        """Lazy-init Chroma client and collection (sync, run in thread)."""
        import os
        try:
            import chromadb
            persist_dir = settings.vector_store_path
            os.makedirs(persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(path=persist_dir)
            self._collection = self._client.get_or_create_collection(
                name="knowledge_vectors",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Vector storage initialized: Chroma at {persist_dir}")
        except ImportError:
            logger.warning("chromadb not installed; vector storage disabled (pip install chromadb)")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Chroma: {e}; vector storage disabled")
            self.enabled = False

    def _ensure_collection(self):
        """Ensure collection is available (re-initialize if needed)."""
        if self.enabled and self._collection is None:
            self._init_chroma()

    # ========== Write operations ==========

    async def upsert_knowledge(self, knowledge: KnowledgeUnit, embedding: List[float]) -> None:
        """Store or update a knowledge item's embedding in the vector store."""
        if not self.enabled:
            return
        self._ensure_collection()
        if self._collection is None:
            return

        def _upsert():
            self._collection.upsert(
                ids=[str(knowledge.id)],
                embeddings=[embedding],
                metadatas=[{
                    "title": knowledge.title,
                    "status": knowledge.status.value if knowledge.status else "draft",
                    "category": knowledge.category or "",
                    "tags": ",".join(knowledge.tags or []),
                }],
                documents=[f"{knowledge.title}\n{knowledge.content[:500]}"],
            )

        await asyncio.to_thread(_upsert)
        logger.info(f"Upserted vector for knowledge {knowledge.id}")

    async def delete_knowledge(self, knowledge_id: UUID) -> None:
        """Remove a knowledge item's vector from the store."""
        if not self.enabled:
            return
        self._ensure_collection()
        if self._collection is None:
            return

        def _delete():
            self._collection.delete(ids=[str(knowledge_id)])

        await asyncio.to_thread(_delete)

    # ========== Read operations ==========

    async def semantic_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar knowledge by embedding.

        Returns:
            List of dicts with keys: id, score (0-1 cosine similarity), title, status, category
            Score is converted from Chroma's L2/cosine distance to a 0-1 similarity value.
        """
        if not self.enabled:
            return []
        self._ensure_collection()
        if self._collection is None:
            return []

        # Build where filter for category
        where = {"category": category} if category else None

        def _search():
            return self._collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where,
            )

        try:
            result = await asyncio.to_thread(_search)
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

        if not result or not result.get("ids") or not result["ids"][0]:
            return []

        ids = result["ids"][0]
        distances = result["distances"][0] if result.get("distances") else []
        metadatas = result.get("metadatas", [None])[0] or [None] * len(ids)
        documents = result.get("documents", [None])[0] or [None] * len(ids)

        items = []
        for i, kid in enumerate(ids):
            dist = distances[i] if i < len(distances) else 1.0
            # Cosine distance → similarity: sim = 1 - dist (Chroma uses L2 by default,
            # but we set hnsw:space=cosine so dist is in [0, 2]; sim = 1 - dist/2 * 2)
            similarity = max(0.0, min(1.0, 1.0 - dist))

            meta = metadatas[i] if i < len(metadatas) and metadatas[i] else {}
            doc = documents[i] if i < len(documents) and documents[i] else ""

            items.append({
                "id": kid,
                "score": round(similarity, 4),
                "title": meta.get("title", ""),
                "status": meta.get("status", ""),
                "category": meta.get("category", ""),
                "content_preview": doc[:200] if doc else "",
            })

        return items

    async def index_count(self) -> int:
        """Return number of items in the vector store."""
        if not self.enabled:
            return 0
        self._ensure_collection()
        if self._collection is None:
            return 0
        try:
            return await asyncio.to_thread(self._collection.count)
        except Exception:
            return 0

    # ========== Bulk indexing ==========

    async def index_all(self, knowledge_service, embed_fn) -> Dict[str, Any]:
        """Re-index all knowledge items into the vector store.

        Args:
            knowledge_service: Instance with .list_knowledge() and .get_knowledge()
            embed_fn: Async callable (text) -> List[float]

        Returns:
            {"indexed": int, "errors": int}
        """
        if not self.enabled:
            return {"indexed": 0, "errors": 0}
        self._ensure_collection()
        if self._collection is None:
            return {"indexed": 0, "errors": 0}

        all_knowledge, _ = await knowledge_service.list_knowledge(page=1, page_size=10000)
        indexed = 0
        errors = 0

        for knowledge in all_knowledge:
            if knowledge.status.value in ("archived", "deleted"):
                continue
            text = f"{knowledge.title}\n{(knowledge.summary or '')}\n{knowledge.content[:500]}"
            try:
                embedding = await embed_fn(text)
                await self.upsert_knowledge(knowledge, embedding)
                indexed += 1
            except Exception as e:
                logger.warning(f"Failed to index knowledge {knowledge.id}: {e}")
                errors += 1

        logger.info(f"Vector index complete: {indexed} indexed, {errors} errors")
        return {"indexed": indexed, "errors": errors}


# Singleton
vector_storage = VectorStorage()
