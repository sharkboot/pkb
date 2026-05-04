import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from uuid6 import uuid6
from datetime import datetime
from storage.markdown_storage import MarkdownStorage
from models.schemas import ContentCollectRequest, KnowledgeUnit
from models.enums import SourceType, KnowledgeStatus
from services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)

class ContentService:
    def __init__(self):
        self.storage = MarkdownStorage()
        self.knowledge_service = KnowledgeService()

    async def collect(self, request: ContentCollectRequest) -> KnowledgeUnit:
        logger.info(f"接收到内容收集请求，类型: {request.source_type}")
        title = self._generate_title(request)
        content = self._build_content(request)
        
        from models.schemas import KnowledgeCreateRequest
        create_request = KnowledgeCreateRequest(
            title=title,
            content=content,
            tags=self._extract_tags(request),
        )
        
        knowledge = await self.knowledge_service.create_knowledge(create_request)
        logger.info(f"知识创建成功，ID: {knowledge.id}")
        await self._trigger_auto_process(knowledge.id, request.source_type)
        
        return knowledge

    def _generate_title(self, request: ContentCollectRequest) -> str:
        if request.content and len(request.content) > 0:
            lines = request.content.strip().split("\n")
            for line in lines:
                if line.strip():
                    return line.strip()[:100]
        return f"知识记录 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    def _build_content(self, request: ContentCollectRequest) -> str:
        parts = []
        
        if request.content:
            parts.append(request.content)
        
        if request.images:
            parts.append("\n## 图片")
            for img_url in request.images:
                parts.append(f"![图片]({img_url})")
        
        if request.attachments:
            parts.append("\n## 附件")
            for attachment in request.attachments:
                parts.append(f"- [{attachment}]({attachment})")
        
        if request.metadata:
            parts.append("\n## 元信息")
            for key, value in request.metadata.items():
                parts.append(f"- {key}: {value}")
        
        return "\n".join(parts)

    def _extract_tags(self, request: ContentCollectRequest) -> List[str]:
        tags = []
        source_tag = request.source_type.value
        if source_tag:
            tags.append(source_tag)
        
        if request.metadata and isinstance(request.metadata, dict):
            source = request.metadata.get("source")
            if source:
                tags.append(source)
        
        return tags

    async def _trigger_auto_process(self, knowledge_id: UUID, source_type: SourceType):
        logger.info(f"触发自动处理，知识ID: {knowledge_id}，类型: {source_type}")
        from services.task_service import TaskService, TaskCreateRequest, TaskType
        task_service = TaskService()
        
        if source_type in [SourceType.SCREENSHOT, SourceType.IMAGE]:
            logger.info("创建 OCR 任务")
            await task_service.create_task(TaskCreateRequest(
                task_type=TaskType.OCR,
                target_id=str(knowledge_id),
            ))
        
        logger.info("创建 SUMMARY 任务")
        await task_service.create_task(TaskCreateRequest(
            task_type=TaskType.SUMMARY,
            target_id=str(knowledge_id),
        ))