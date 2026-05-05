import os
import asyncio
import json
from typing import List, Optional, Any, Tuple, Dict
from uuid import UUID
from uuid6 import uuid6
from datetime import datetime
import frontmatter
from storage.base_storage import BaseStorage
from models.schemas import KnowledgeUnit, Session, Task, Category
from models.enums import KnowledgeStatus
from core.config import settings


class CatalogEntry:
    """目录条目"""
    def __init__(
        self,
        id: UUID,
        title: str,
        summary: Optional[str],
        content_preview: str,
        tags: List[str],
        category: Optional[str],
        file_path: str,
        status: KnowledgeStatus,
        created_at: datetime,
        updated_at: datetime,
    ):
        self.id = id
        self.title = title
        self.summary = summary
        self.content_preview = content_preview
        self.tags = tags
        self.category = category
        self.file_path = file_path
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "title": self.title,
            "summary": self.summary,
            "content_preview": self.content_preview,
            "tags": self.tags,
            "category": self.category,
            "file_path": self.file_path,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CatalogEntry":
        return cls(
            id=UUID(data["id"]),
            title=data.get("title", ""),
            summary=data.get("summary"),
            content_preview=data.get("content_preview", ""),
            tags=data.get("tags", []),
            category=data.get("category"),
            file_path=data.get("file_path", ""),
            status=KnowledgeStatus(data.get("status", "draft")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    def match(self, keyword: str) -> bool:
        """判断是否匹配关键词"""
        kw = keyword.lower()
        return (
            kw in self.title.lower()
            or kw in (self.summary or "").lower()
            or kw in self.content_preview.lower()
            or any(kw in tag.lower() for tag in self.tags)
            or (self.category and kw in self.category.lower())
        )


class MarkdownStorage(BaseStorage):
    def __init__(self):
        self.base_path = settings.knowledge_base_path
        self._catalog_path = os.path.join(self.base_path, "catalog.json")
        self._init_directories()

    def _init_directories(self):
        directories = [
            self.base_path,
            os.path.join(self.base_path, "inbox"),
            os.path.join(self.base_path, "fleeting_notes"),
            os.path.join(self.base_path, "literature_notes"),
            os.path.join(self.base_path, "permanent_notes"),
            os.path.join(self.base_path, "project_notes"),
            os.path.join(self.base_path, "summaries"),
            os.path.join(self.base_path, "summaries", "daily"),
            os.path.join(self.base_path, "summaries", "weekly"),
            os.path.join(self.base_path, "summaries", "monthly"),
            os.path.join(self.base_path, "archive"),
            os.path.join(self.base_path, "sessions"),
            os.path.join(self.base_path, "tasks"),
            os.path.join(self.base_path, "categories"),
        ]
        for dir_path in directories:
            os.makedirs(dir_path, exist_ok=True)

    # ========== 目录索引管理 ==========

    def _load_catalog(self) -> Dict[str, CatalogEntry]:
        """加载目录索引"""
        if not os.path.exists(self._catalog_path):
            return {}
        try:
            with open(self._catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 支持新旧两种格式：新格式有 entries 字段，旧格式直接是列表
            if isinstance(data, dict) and "entries" in data:
                entries = data["entries"]
            elif isinstance(data, list):
                entries = data
            else:
                return {}
            return {entry["id"]: CatalogEntry.from_dict(entry) for entry in entries}
        except Exception:
            return {}

    def _save_catalog(self, catalog: Dict[str, CatalogEntry]):
        """保存目录索引"""
        data = list(entry.to_dict() for entry in catalog.values())
        loop = asyncio.get_event_loop()
        loop.run_in_executor(
            None,
            self._write_json,
            self._catalog_path,
            {"version": 1, "entries": data}
        )

    def _update_catalog(self, knowledge: KnowledgeUnit):
        """更新单条目录条目"""
        catalog = self._load_catalog()
        status_path = self._get_status_path(knowledge.status)
        file_path = os.path.join(status_path, f"{knowledge.id}.md")

        # 内容预览：取前200字
        content_preview = knowledge.content[:200] if knowledge.content else ""

        entry = CatalogEntry(
            id=knowledge.id,
            title=knowledge.title,
            summary=knowledge.summary,
            content_preview=content_preview,
            tags=knowledge.tags or [],
            category=knowledge.category,
            file_path=file_path,
            status=knowledge.status,
            created_at=knowledge.created_at,
            updated_at=knowledge.updated_at,
        )
        catalog[str(knowledge.id)] = entry
        self._save_catalog(catalog)

    def _remove_from_catalog(self, knowledge_id: UUID):
        """从目录中移除条目"""
        catalog = self._load_catalog()
        if str(knowledge_id) in catalog:
            del catalog[str(knowledge_id)]
            self._save_catalog(catalog)

    async def search_catalog(
        self,
        keyword: str = "",
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[CatalogEntry]:
        """搜索目录索引，不过滤直接返回全部条目（让模型做筛选）"""
        catalog = self._load_catalog()
        results = []

        for entry in catalog.values():
            if category and entry.category != category:
                continue
            # 跳过 keyword 过滤，让调用方用模型筛选
            results.append(entry)

        results.sort(key=lambda x: x.updated_at, reverse=True)
        return results[:limit]

    async def rebuild_catalog(self):
        """重建整个目录索引"""
        catalog: Dict[str, CatalogEntry] = {}

        for status in KnowledgeStatus:
            dir_path = self._get_status_path(status)
            if os.path.exists(dir_path):
                for filename in os.listdir(dir_path):
                    if filename.endswith(".md"):
                        file_path = os.path.join(dir_path, filename)
                        try:
                            loop = asyncio.get_event_loop()
                            post = await loop.run_in_executor(
                                None, self._read_frontmatter, file_path
                            )
                            content_preview = post.content[:200] if post.content else ""

                            entry = CatalogEntry(
                                id=UUID(post.get("id")),
                                title=post.get("title", ""),
                                summary=post.get("summary"),
                                content_preview=content_preview,
                                tags=post.get("tags", []),
                                category=post.get("category"),
                                file_path=file_path,
                                status=KnowledgeStatus(post.get("status", "draft")),
                                created_at=datetime.fromisoformat(post.get("created_at")),
                                updated_at=datetime.fromisoformat(post.get("updated_at")),
                            )
                            catalog[str(entry.id)] = entry
                        except Exception:
                            continue

        self._save_catalog(catalog)
        return len(catalog)

    def _get_knowledge_path(self, knowledge_id: UUID) -> str:
        return os.path.join(self.base_path, "permanent_notes", f"{knowledge_id}.md")

    def _get_status_path(self, status: KnowledgeStatus) -> str:
        status_map = {
            KnowledgeStatus.DRAFT: "inbox",
            KnowledgeStatus.ACTIVE: "permanent_notes",
            KnowledgeStatus.ARCHIVED: "archive",
            KnowledgeStatus.DELETED: "archive",
        }
        return os.path.join(self.base_path, status_map.get(status, "inbox"))

    async def save_knowledge(self, knowledge: KnowledgeUnit) -> str:
        file_path = os.path.join(self._get_status_path(knowledge.status), f"{knowledge.id}.md")

        metadata = {
            "id": str(knowledge.id),
            "title": knowledge.title,
            "tags": knowledge.tags,
            "category": knowledge.category,
            "source": knowledge.source,
            "score": knowledge.score,
            "related": knowledge.relations,
            "created_at": knowledge.created_at.isoformat(),
            "updated_at": knowledge.updated_at.isoformat(),
            "status": knowledge.status.value,
        }

        if knowledge.summary:
            metadata["summary"] = knowledge.summary

        post = frontmatter.Post(knowledge.content, **metadata)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._write_frontmatter, file_path, post)

        # 更新目录索引
        self._update_catalog(knowledge)

        return file_path

    def _write_frontmatter(self, file_path: str, post: frontmatter.Post):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    def _read_frontmatter(self, file_path: str) -> frontmatter.Post:
        with open(file_path, "r", encoding="utf-8") as f:
            return frontmatter.load(f)

    async def get_knowledge(self, knowledge_id: UUID) -> Optional[KnowledgeUnit]:
        for status in KnowledgeStatus:
            file_path = os.path.join(self._get_status_path(status), f"{knowledge_id}.md")
            if os.path.exists(file_path):
                return await self._parse_knowledge_file(file_path)
        return None

    async def _parse_knowledge_file(self, file_path: str) -> KnowledgeUnit:
        loop = asyncio.get_event_loop()
        post = await loop.run_in_executor(None, self._read_frontmatter, file_path)
        
        return KnowledgeUnit(
            id=UUID(post.get("id")),
            title=post.get("title", ""),
            summary=post.get("summary"),
            content=post.content,
            source_refs=[],
            tags=post.get("tags", []),
            relations=post.get("related", []),
            status=KnowledgeStatus(post.get("status", "draft")),
            category=post.get("category"),
            source=post.get("source"),
            score=post.get("score", 0.0),
            created_at=datetime.fromisoformat(post.get("created_at")),
            updated_at=datetime.fromisoformat(post.get("updated_at")),
        )

    async def update_knowledge(self, knowledge_id: UUID, updates: dict) -> bool:
        knowledge = await self.get_knowledge(knowledge_id)
        if not knowledge:
            return False

        for key, value in updates.items():
            if hasattr(knowledge, key):
                setattr(knowledge, key, value)

        knowledge.updated_at = datetime.now()
        await self.save_knowledge(knowledge)
        # save_knowledge 已包含 _update_catalog
        return True

    async def delete_knowledge(self, knowledge_id: UUID) -> bool:
        knowledge = await self.get_knowledge(knowledge_id)
        if not knowledge:
            return False

        self._remove_from_catalog(knowledge_id)
        return await self.update_knowledge(knowledge_id, {"status": KnowledgeStatus.DELETED})

    async def list_knowledge(
        self,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[KnowledgeUnit], int]:
        all_knowledge = []

        for status in KnowledgeStatus:
            dir_path = self._get_status_path(status)
            if os.path.exists(dir_path):
                for filename in os.listdir(dir_path):
                    if filename.endswith(".md"):
                        file_path = os.path.join(dir_path, filename)
                        try:
                            knowledge = await self._parse_knowledge_file(file_path)

                            if category and knowledge.category != category:
                                continue
                            if keyword and keyword.lower() not in knowledge.title.lower() and keyword.lower() not in knowledge.content.lower():
                                continue

                            all_knowledge.append(knowledge)
                        except Exception:
                            continue

        all_knowledge.sort(key=lambda x: x.updated_at, reverse=True)

        total = len(all_knowledge)
        start = (page - 1) * page_size
        end = start + page_size

        return all_knowledge[start:end], total

    async def search_knowledge(
        self,
        keyword: str,
        category: Optional[str] = None,
        use_catalog: bool = True,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[KnowledgeUnit], int, List[CatalogEntry]]:
        """两阶段搜索：目录粗筛 + 文件精查

        Args:
            keyword: 搜索关键词
            category: 可选，限定分类
            use_catalog: 是否使用目录索引（True=快速粗筛，False=全量扫描）
            page: 页码
            page_size: 每页数量

        Returns:
            (知识列表, 总数, 匹配的目录条目)
        """
        if use_catalog:
            # 第一阶段：搜索目录索引
            catalog_entries = await self.search_catalog(keyword, category, limit=100)
            matched_ids = [entry.id for entry in catalog_entries]

            # 第二阶段：根据目录匹配结果加载完整知识
            results = []
            for kid in matched_ids:
                knowledge = await self.get_knowledge(kid)
                if knowledge:
                    results.append(knowledge)

            results.sort(key=lambda x: x.updated_at, reverse=True)
            total = len(results)
            start = (page - 1) * page_size
            end = start + page_size
            return results[start:end], total, catalog_entries[start:end]
        else:
            # 不使用目录，全量扫描
            all_knowledge, total = await self.list_knowledge(
                category=category,
                keyword=keyword,
                page=page,
                page_size=page_size
            )
            return all_knowledge, total, []

    async def get_knowledge_by_path(self, file_path: str) -> Optional[KnowledgeUnit]:
        """根据文件路径加载知识"""
        if not os.path.exists(file_path):
            return None
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._parse_knowledge_file_static, file_path)
        except Exception:
            return None

    @staticmethod
    def _parse_knowledge_file_static(file_path: str) -> KnowledgeUnit:
        """静态方法：解析知识文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        return KnowledgeUnit(
            id=UUID(post.get("id")),
            title=post.get("title", ""),
            summary=post.get("summary"),
            content=post.content,
            source_refs=[],
            tags=post.get("tags", []),
            relations=post.get("related", []),
            status=KnowledgeStatus(post.get("status", "draft")),
            category=post.get("category"),
            source=post.get("source"),
            score=post.get("score", 0.0),
            created_at=datetime.fromisoformat(post.get("created_at")),
            updated_at=datetime.fromisoformat(post.get("updated_at")),
        )

    def _get_session_path(self, session_id: UUID) -> str:
        return os.path.join(self.base_path, "sessions", f"{session_id}.json")

    async def save_session(self, session: Session) -> str:
        import json
        file_path = self._get_session_path(session.id)
        
        data = {
            "id": str(session.id),
            "title": session.title,
            "context": session.context,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._write_json, file_path, data)
        
        return file_path

    def _write_json(self, file_path: str, data: dict):
        import json
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _read_json(self, file_path: str) -> dict:
        import json
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def get_session(self, session_id: UUID) -> Optional[Session]:
        file_path = self._get_session_path(session_id)
        if not os.path.exists(file_path):
            return None
        
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, self._read_json, file_path)
        
        return Session(
            id=UUID(data["id"]),
            title=data.get("title"),
            context=data.get("context"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    async def list_sessions(self) -> List[Session]:
        sessions_dir = os.path.join(self.base_path, "sessions")
        sessions = []
        
        if os.path.exists(sessions_dir):
            for filename in os.listdir(sessions_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(sessions_dir, filename)
                    try:
                        loop = asyncio.get_event_loop()
                        data = await loop.run_in_executor(None, self._read_json, file_path)
                        sessions.append(Session(
                            id=UUID(data["id"]),
                            title=data.get("title"),
                            context=data.get("context"),
                            created_at=datetime.fromisoformat(data["created_at"]),
                            updated_at=datetime.fromisoformat(data["updated_at"]),
                        ))
                    except Exception:
                        continue
        
        return sorted(sessions, key=lambda x: x.updated_at, reverse=True)

    async def delete_session(self, session_id: UUID) -> bool:
        file_path = self._get_session_path(session_id)
        if not os.path.exists(file_path):
            return False
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, os.remove, file_path)
        return True

    def _get_task_path(self, task_id: UUID) -> str:
        return os.path.join(self.base_path, "tasks", f"{task_id}.json")

    async def save_task(self, task: Task) -> str:
        file_path = self._get_task_path(task.id)
        
        data = {
            "id": str(task.id),
            "task_type": task.task_type.value,
            "target_id": task.target_id,
            "params": task.params,
            "status": task.status,
            "result": task.result,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._write_json, file_path, data)
        
        return file_path

    async def get_task(self, task_id: UUID) -> Optional[Task]:
        file_path = self._get_task_path(task_id)
        if not os.path.exists(file_path):
            return None
        
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, self._read_json, file_path)
        
        from models.enums import TaskType
        return Task(
            id=UUID(data["id"]),
            task_type=TaskType(data["task_type"]),
            target_id=data.get("target_id"),
            params=data.get("params"),
            status=data.get("status", "pending"),
            result=data.get("result"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    async def list_tasks(self) -> List[Task]:
        tasks_dir = os.path.join(self.base_path, "tasks")
        tasks = []
        
        if os.path.exists(tasks_dir):
            for filename in os.listdir(tasks_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(tasks_dir, filename)
                    try:
                        loop = asyncio.get_event_loop()
                        data = await loop.run_in_executor(None, self._read_json, file_path)
                        from models.enums import TaskType
                        tasks.append(Task(
                            id=UUID(data["id"]),
                            task_type=TaskType(data["task_type"]),
                            target_id=data.get("target_id"),
                            params=data.get("params"),
                            status=data.get("status", "pending"),
                            result=data.get("result"),
                            created_at=datetime.fromisoformat(data["created_at"]),
                            updated_at=datetime.fromisoformat(data["updated_at"]),
                        ))
                    except Exception:
                        continue
        
        return sorted(tasks, key=lambda x: x.created_at, reverse=True)

    async def update_task(self, task_id: UUID, updates: dict) -> bool:
        task = await self.get_task(task_id)
        if not task:
            return False

        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        task.updated_at = datetime.now()
        await self.save_task(task)
        return True

    def _get_category_path(self, category_id: UUID) -> str:
        return os.path.join(self.base_path, "categories", f"{category_id}.json")

    async def save_category(self, category: Category) -> str:
        file_path = self._get_category_path(category.id)
        
        data = {
            "id": str(category.id),
            "name": category.name,
            "parent_id": str(category.parent_id) if category.parent_id else None,
            "created_at": category.created_at.isoformat(),
            "updated_at": category.updated_at.isoformat(),
        }
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._write_json, file_path, data)
        
        return file_path

    async def get_category(self, category_id: UUID) -> Optional[Category]:
        file_path = self._get_category_path(category_id)
        if not os.path.exists(file_path):
            return None
        
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, self._read_json, file_path)
        
        return Category(
            id=UUID(data["id"]),
            name=data["name"],
            parent_id=UUID(data["parent_id"]) if data.get("parent_id") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    async def list_categories(self) -> List[Category]:
        categories_dir = os.path.join(self.base_path, "categories")
        categories = []
        
        if os.path.exists(categories_dir):
            for filename in os.listdir(categories_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(categories_dir, filename)
                    try:
                        loop = asyncio.get_event_loop()
                        data = await loop.run_in_executor(None, self._read_json, file_path)
                        categories.append(Category(
                            id=UUID(data["id"]),
                            name=data["name"],
                            parent_id=UUID(data["parent_id"]) if data.get("parent_id") else None,
                            created_at=datetime.fromisoformat(data["created_at"]),
                            updated_at=datetime.fromisoformat(data["updated_at"]),
                        ))
                    except Exception:
                        continue
        
        return sorted(categories, key=lambda x: x.name)

    async def delete_category(self, category_id: UUID) -> bool:
        file_path = self._get_category_path(category_id)
        if not os.path.exists(file_path):
            return False
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, os.remove, file_path)
        return True