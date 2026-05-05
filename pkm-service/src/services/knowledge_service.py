from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from uuid6 import uuid6
from datetime import datetime
from storage.markdown_storage import MarkdownStorage
from models.schemas import KnowledgeUnit, KnowledgeCreateRequest, KnowledgeUpdateRequest
from models.enums import KnowledgeStatus, SourceType
from models.exceptions import ResourceNotFoundException
from llm.provider import chat_completion

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

    async def search_knowledge(
        self,
        keyword: str,
        category: Optional[str] = None,
        use_catalog: bool = True,
        page: int = 1,
        page_size: int = 20
    ):
        return await self.storage.search_knowledge(keyword, category, use_catalog, page, page_size)

    async def search_catalog(
        self,
        keyword: str,
        category: Optional[str] = None,
        limit: int = 50
    ):
        return await self.storage.search_catalog(keyword, category, limit)

    async def rebuild_catalog(self) -> int:
        return await self.storage.rebuild_catalog()

    async def smart_search(self, query: str) -> Dict[str, Any]:
        """智能搜索：把用户查询和目录一起给模型，让模型筛选相关条目"""
        import json
        import re

        # Step 1: 获取目录中的所有条目（不过滤，让模型筛选）
        catalog_entries = await self.storage.search_catalog(
            keyword="",
            category=None,
            limit=1000  # 获取足够多的条目给模型筛选
        )

        if not catalog_entries:
            return {
                "query": query,
                "relevantIds": [],
                "results": [],
                "total": 0,
                "reason": "目录为空",
            }

        # Step 2: 构造提示词，把目录条目和用户查询一起给模型
        entries_text = "\n".join([
            f"ID: {e.id} | 标题: {e.title} | 摘要: {e.summary or '(无)'} | 内容预览: {e.content_preview[:50] if e.content_preview else '(无)'}"
            for e in catalog_entries
        ])

        match_prompt = f"""你是一个知识库检索助手。用户输入了一条查询，请从以下目录条目中找出与用户查询相关的条目。

用户查询："{query}"

目录条目：
{entries_text}

请分析用户查询，从目录中找出最相关的条目。注意：
1. 要理解用户的真实意图，不仅仅是关键词匹配
2. 即使目录条目中没有直接提到查询词，只要主题相关也应该选中
3. 如果有多个相关条目，全部选出来

请以 JSON 格式返回：
{{
  "relevant_ids": ["相关条目ID1", "相关条目ID2", ...],
  "reason": "简要说明为什么这些条目相关"
}}

只返回 JSON，不要有其他内容。"""

        try:
            match_result = await chat_completion(
                messages=[{"role": "user", "content": match_prompt}]
            )

            json_match = re.search(r'\{.*\}', match_result, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = {"relevant_ids": [], "reason": ""}
        except Exception as e:
            analysis = {"relevant_ids": [], "reason": f"匹配失败: {str(e)}"}

        relevant_ids = analysis.get("relevant_ids", [])

        # Step 3: 根据返回的 ID 获取完整知识条目
        results = []
        for entry_id in relevant_ids:
            try:
                knowledge = await self.get_knowledge(UUID(entry_id))
                if knowledge:
                    results.append(knowledge)
            except Exception:
                continue

        return {
            "query": query,
            "reason": analysis.get("reason", ""),
            "relevantIds": relevant_ids,
            "results": results,
            "total": len(results),
        }

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