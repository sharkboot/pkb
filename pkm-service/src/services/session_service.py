from typing import List, Optional, Dict, Any
from uuid import UUID
from uuid6 import uuid6
from datetime import datetime
from storage.markdown_storage import MarkdownStorage
from models.schemas import Session, SessionCreateRequest
from models.exceptions import ResourceNotFoundException

class SessionService:
    def __init__(self):
        self.storage = MarkdownStorage()

    async def create_session(self, request: SessionCreateRequest) -> Session:
        now = datetime.now()
        session = Session(
            id=uuid6(),
            title=request.title or f"会话 {now.strftime('%Y-%m-%d %H:%M')}",
            context={},
            created_at=now,
            updated_at=now,
        )
        
        await self.storage.save_session(session)
        return session

    async def get_session(self, session_id: UUID) -> Session:
        session = await self.storage.get_session(session_id)
        if not session:
            raise ResourceNotFoundException(f"会话 {session_id} 不存在")
        return session

    async def list_sessions(self) -> List[Session]:
        return await self.storage.list_sessions()

    async def delete_session(self, session_id: UUID) -> bool:
        session = await self.storage.get_session(session_id)
        if not session:
            raise ResourceNotFoundException(f"会话 {session_id} 不存在")
        
        return await self.storage.delete_session(session_id)

    async def update_context(self, session_id: UUID, context: Dict[str, Any]) -> Session:
        session = await self.get_session(session_id)
        session.context = context
        session.updated_at = datetime.now()
        await self.storage.save_session(session)
        return session