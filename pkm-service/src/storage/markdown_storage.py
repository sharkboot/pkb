import os
import asyncio
from typing import List, Optional, Any, Tuple, Dict
from uuid import UUID
from uuid6 import uuid6
from datetime import datetime
import frontmatter
from storage.base_storage import BaseStorage
from models.schemas import KnowledgeUnit, Session, Task, Category
from models.enums import KnowledgeStatus
from core.config import settings

class MarkdownStorage(BaseStorage):
    def __init__(self):
        self.base_path = settings.knowledge_base_path
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
        return True

    async def delete_knowledge(self, knowledge_id: UUID) -> bool:
        knowledge = await self.get_knowledge(knowledge_id)
        if not knowledge:
            return False

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