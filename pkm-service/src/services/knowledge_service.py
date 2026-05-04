from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from uuid6 import uuid6
from datetime import datetime
from storage.markdown_storage import MarkdownStorage
from models.schemas import KnowledgeUnit, KnowledgeCreateRequest, KnowledgeUpdateRequest
from models.enums import KnowledgeStatus, SourceType
from models.exceptions import ResourceNotFoundException

class KnowledgeService:
    def __init__(self):
        self.storage = MarkdownStorage()

    async def create_knowledge(self, request: KnowledgeCreateRequest) -> KnowledgeUnit:
        now = datetime.now()
        knowledge = KnowledgeUnit(
            id=uuid6(),
            title=request.title,
            summary=request.summary,
            content=request.content,
            source_refs=request.source_refs or [],
            tags=request.tags or [],
            relations=request.relations or [],
            status=request.status or KnowledgeStatus.DRAFT,
            score=0.0,
            created_at=now,
            updated_at=now,
        )
        
        await self.storage.save_knowledge(knowledge)
        return knowledge

    async def get_knowledge(self, knowledge_id: UUID) -> KnowledgeUnit:
        knowledge = await self.storage.get_knowledge(knowledge_id)
        if not knowledge:
            raise ResourceNotFoundException(f"知识单元 {knowledge_id} 不存在")
        return knowledge

    async def update_knowledge(self, knowledge_id: UUID, request: KnowledgeUpdateRequest) -> KnowledgeUnit:
        updates = {}
        if request.title:
            updates["title"] = request.title
        if request.summary:
            updates["summary"] = request.summary
        if request.content:
            updates["content"] = request.content
        if request.tags is not None:
            updates["tags"] = request.tags
        if request.relations is not None:
            updates["relations"] = request.relations
        if request.status:
            updates["status"] = request.status
        if request.category:
            updates["category"] = request.category
        
        success = await self.storage.update_knowledge(knowledge_id, updates)
        if not success:
            raise ResourceNotFoundException(f"知识单元 {knowledge_id} 不存在")
        
        return await self.get_knowledge(knowledge_id)

    async def delete_knowledge(self, knowledge_id: UUID) -> bool:
        knowledge = await self.storage.get_knowledge(knowledge_id)
        if not knowledge:
            raise ResourceNotFoundException(f"知识单元 {knowledge_id} 不存在")
        
        return await self.storage.delete_knowledge(knowledge_id)

    async def list_knowledge(
        self,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[KnowledgeUnit], int]:
        return await self.storage.list_knowledge(category, keyword, page, page_size)

    async def star_knowledge(self, knowledge_id: UUID) -> KnowledgeUnit:
        knowledge = await self.get_knowledge(knowledge_id)
        knowledge.score = min(1.0, knowledge.score + 0.1)
        await self.storage.update_knowledge(knowledge_id, {"score": knowledge.score})
        return knowledge

    async def restore_knowledge(self, knowledge_id: UUID) -> KnowledgeUnit:
        knowledge = await self.get_knowledge(knowledge_id)
        if knowledge.status != KnowledgeStatus.DELETED:
            return knowledge
        
        await self.storage.update_knowledge(knowledge_id, {"status": KnowledgeStatus.DRAFT})
        return await self.get_knowledge(knowledge_id)

    async def permanent_delete(self, knowledge_id: UUID) -> bool:
        knowledge = await self.storage.get_knowledge(knowledge_id)
        if not knowledge:
            raise ResourceNotFoundException(f"知识单元 {knowledge_id} 不存在")
        
        import os
        for status in KnowledgeStatus:
            dir_path = os.path.join(self.storage.base_path, self.storage._get_status_path(status).replace(self.storage.base_path, "").lstrip(os.sep))
            file_path = os.path.join(self.storage.base_path, dir_path, f"{knowledge_id}.md")
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        
        return False