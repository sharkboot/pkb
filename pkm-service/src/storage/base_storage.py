from abc import ABC, abstractmethod
from typing import List, Optional, Any
from uuid import UUID
from models.schemas import KnowledgeUnit, Session, Task, Category

class BaseStorage(ABC):
    @abstractmethod
    async def save_knowledge(self, knowledge: KnowledgeUnit) -> str:
        pass

    @abstractmethod
    async def get_knowledge(self, knowledge_id: UUID) -> Optional[KnowledgeUnit]:
        pass

    @abstractmethod
    async def update_knowledge(self, knowledge_id: UUID, updates: dict) -> bool:
        pass

    @abstractmethod
    async def delete_knowledge(self, knowledge_id: UUID) -> bool:
        pass

    @abstractmethod
    async def list_knowledge(
        self,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[KnowledgeUnit], int]:
        pass

    @abstractmethod
    async def save_session(self, session: Session) -> str:
        pass

    @abstractmethod
    async def get_session(self, session_id: UUID) -> Optional[Session]:
        pass

    @abstractmethod
    async def list_sessions(self) -> List[Session]:
        pass

    @abstractmethod
    async def delete_session(self, session_id: UUID) -> bool:
        pass

    @abstractmethod
    async def save_task(self, task: Task) -> str:
        pass

    @abstractmethod
    async def get_task(self, task_id: UUID) -> Optional[Task]:
        pass

    @abstractmethod
    async def list_tasks(self) -> List[Task]:
        pass

    @abstractmethod
    async def update_task(self, task_id: UUID, updates: dict) -> bool:
        pass

    @abstractmethod
    async def save_category(self, category: Category) -> str:
        pass

    @abstractmethod
    async def get_category(self, category_id: UUID) -> Optional[Category]:
        pass

    @abstractmethod
    async def list_categories(self) -> List[Category]:
        pass

    @abstractmethod
    async def delete_category(self, category_id: UUID) -> bool:
        pass