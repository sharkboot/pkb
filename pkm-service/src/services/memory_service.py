import os
import re
import json
import asyncio
import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from uuid6 import uuid6
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from storage.markdown_storage import MarkdownStorage
from models.schemas import KnowledgeUnit, KnowledgeCreateRequest
from models.enums import KnowledgeStatus
from llm.provider import chat_completion, create_embedding, create_embedding_cached, create_embeddings
from core.config import settings

logger = logging.getLogger(__name__)


class SummaryType(str, Enum):
    """Summary type enumeration"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class MergeResult:
    """Result of a merge operation"""
    merged_count: int = 0
    deleted_count: int = 0
    created_knowledge: Optional[KnowledgeUnit] = None
    merged_ids: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class DeduplicationResult:
    """Result of a deduplication operation"""
    checked_count: int = 0
    duplicate_groups: List[Dict[str, Any]] = field(default_factory=list)
    removed_count: int = 0
    error: Optional[str] = None


@dataclass
class SummaryResult:
    """Result of a summary generation"""
    summary_id: Optional[str] = None
    summary_type: Optional[SummaryType] = None
    content: str = ""
    knowledge_count: int = 0
    error: Optional[str] = None


@dataclass
class MemoryIntegrationStatus:
    """Current status of memory integration"""
    last_merge_time: Optional[datetime] = None
    last_dedup_time: Optional[datetime] = None
    last_summary_time: Optional[datetime] = None
    daily_schedule_enabled: bool = False
    weekly_schedule_enabled: bool = False
    monthly_schedule_enabled: bool = False
    daily_schedule_time: str = "09:00"
    weekly_schedule_day: int = 0  # 0=Monday
    weekly_schedule_time: str = "09:00"
    monthly_schedule_day: int = 1
    monthly_schedule_time: str = "09:00"


class MemoryService:
    """
    Memory integration service for PKM system.
    
    Handles:
    - Knowledge merging (combining similar content)
    - Deduplication (detecting and removing duplicates)
    - Relation building (automatically linking related knowledge)
    - Periodic summaries (daily/weekly/monthly)
    """

    def __init__(self):
        self.storage = MarkdownStorage()
        self._status_file = os.path.join(settings.knowledge_base_path, "memory_status.json")
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(os.path.join(settings.knowledge_base_path, "summaries", "daily"), exist_ok=True)
        os.makedirs(os.path.join(settings.knowledge_base_path, "summaries", "weekly"), exist_ok=True)
        os.makedirs(os.path.join(settings.knowledge_base_path, "summaries", "monthly"), exist_ok=True)

    def _load_status(self) -> MemoryIntegrationStatus:
        """Load memory integration status from file"""
        try:
            if os.path.exists(self._status_file):
                with open(self._status_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return MemoryIntegrationStatus(
                    last_merge_time=datetime.fromisoformat(data["last_merge_time"]) if data.get("last_merge_time") else None,
                    last_dedup_time=datetime.fromisoformat(data["last_dedup_time"]) if data.get("last_dedup_time") else None,
                    last_summary_time=datetime.fromisoformat(data["last_summary_time"]) if data.get("last_summary_time") else None,
                    daily_schedule_enabled=data.get("daily_schedule_enabled", False),
                    weekly_schedule_enabled=data.get("weekly_schedule_enabled", False),
                    monthly_schedule_enabled=data.get("monthly_schedule_enabled", False),
                    daily_schedule_time=data.get("daily_schedule_time", "09:00"),
                    weekly_schedule_day=data.get("weekly_schedule_day", 0),
                    weekly_schedule_time=data.get("weekly_schedule_time", "09:00"),
                    monthly_schedule_day=data.get("monthly_schedule_day", 1),
                    monthly_schedule_time=data.get("monthly_schedule_time", "09:00"),
                )
        except Exception as e:
            logger.warning(f"Failed to load memory status: {e}")
        return MemoryIntegrationStatus()

    def _save_status(self, status: MemoryIntegrationStatus):
        """Save memory integration status to file"""
        try:
            data = {
                "last_merge_time": status.last_merge_time.isoformat() if status.last_merge_time else None,
                "last_dedup_time": status.last_dedup_time.isoformat() if status.last_dedup_time else None,
                "last_summary_time": status.last_summary_time.isoformat() if status.last_summary_time else None,
                "daily_schedule_enabled": status.daily_schedule_enabled,
                "weekly_schedule_enabled": status.weekly_schedule_enabled,
                "monthly_schedule_enabled": status.monthly_schedule_enabled,
                "daily_schedule_time": status.daily_schedule_time,
                "weekly_schedule_day": status.weekly_schedule_day,
                "weekly_schedule_time": status.weekly_schedule_time,
                "monthly_schedule_day": status.monthly_schedule_day,
                "monthly_schedule_time": status.monthly_schedule_time,
            }
            with open(self._status_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memory status: {e}")

    async def get_status(self) -> MemoryIntegrationStatus:
        """Get current memory integration status"""
        return self._load_status()

    async def update_schedule(
        self,
        daily_enabled: Optional[bool] = None,
        weekly_enabled: Optional[bool] = None,
        monthly_enabled: Optional[bool] = None,
        daily_time: Optional[str] = None,
        weekly_day: Optional[int] = None,
        weekly_time: Optional[str] = None,
        monthly_day: Optional[int] = None,
        monthly_time: Optional[str] = None,
    ) -> MemoryIntegrationStatus:
        """Update schedule settings"""
        status = self._load_status()
        
        if daily_enabled is not None:
            status.daily_schedule_enabled = daily_enabled
        if weekly_enabled is not None:
            status.weekly_schedule_enabled = weekly_enabled
        if monthly_enabled is not None:
            status.monthly_schedule_enabled = monthly_enabled
        if daily_time is not None:
            status.daily_schedule_time = daily_time
        if weekly_day is not None:
            status.weekly_schedule_day = weekly_day
        if weekly_time is not None:
            status.weekly_schedule_time = weekly_time
        if monthly_day is not None:
            status.monthly_schedule_day = monthly_day
        if monthly_time is not None:
            status.monthly_schedule_time = monthly_time
        
        self._save_status(status)
        return status

    async def find_similar_knowledge(
        self,
        knowledge: KnowledgeUnit,
        threshold: float = 0.7,
        limit: int = 10,
    ) -> List[Tuple[KnowledgeUnit, float]]:
        """
        Find similar knowledge items using embedding similarity.
        
        Args:
            knowledge: Reference knowledge item
            threshold: Similarity threshold (0-1)
            limit: Maximum number of results
        
        Returns:
            List of (knowledge, similarity_score) tuples
        """
        try:
            # Get all knowledge items
            all_knowledge, _ = await self.storage.list_knowledge(
                page=1,
                page_size=1000
            )
            
            # Filter out the reference knowledge and archived/deleted items
            candidates = [
                k for k in all_knowledge
                if k.id != knowledge.id
                and k.status in [KnowledgeStatus.DRAFT, KnowledgeStatus.ACTIVE]
            ]
            
            if not candidates:
                return []

            # Create embedding for reference knowledge (cached)
            ref_text = f"{knowledge.title}\n{knowledge.summary or ''}\n{knowledge.content[:500]}"
            ref_embedding = await create_embedding_cached(ref_text)

            # Batch-fetch all candidate embeddings in a single request
            candidate_texts = [
                f"{k.title}\n{k.summary or ''}\n{k.content[:500]}"
                for k in candidates
            ]
            candidate_embeddings = await create_embeddings(candidate_texts)

            # Calculate similarities
            similarities = []
            for candidate, candidate_embedding in zip(candidates, candidate_embeddings):
                similarity = self._cosine_similarity(ref_embedding, candidate_embedding)
                if similarity >= threshold:
                    similarities.append((candidate, similarity))

            # Sort by similarity and return top N
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar knowledge: {e}")
            return []

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(a) != len(b) or len(a) == 0:
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(y * y for y in b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)

    async def merge_knowledge(
        self,
        source_ids: List[str],
        auto_delete_duplicates: bool = False,
    ) -> MergeResult:
        """
        Merge multiple knowledge items into one.
        
        Args:
            source_ids: List of knowledge IDs to merge
            auto_delete_duplicates: Whether to delete merged items after merge
        
        Returns:
            MergeResult with operation details
        """
        if len(source_ids) < 2:
            return MergeResult(error="需要至少2条知识才能合并")
        
        try:
            # Load all source knowledge
            sources = []
            for sid in source_ids:
                try:
                    k = await self.storage.get_knowledge(UUID(sid))
                    if k:
                        sources.append(k)
                except Exception:
                    continue
            
            if len(sources) < 2:
                return MergeResult(error="有效知识少于2条")
            
            # Generate merge content using LLM
            merge_prompt = self._build_merge_prompt(sources)
            merged_content = await chat_completion(
                messages=[{"role": "user", "content": merge_prompt}]
            )
            
            # Extract title and tags from merged content
            title_prompt = f"""根据以下合并后的内容，生成一个简洁的标题（不超过30字）和3-5个标签。

内容：
{merged_content[:1000]}

请以JSON格式返回：
{{"title": "标题", "tags": ["标签1", "标签2", "标签3"]}}
只返回JSON，不要其他内容。"""
            
            title_result = await chat_completion(
                messages=[{"role": "user", "content": title_prompt}]
            )
            
            # Parse title and tags
            json_match = re.search(r'\{.*\}', title_result, re.DOTALL)
            if json_match:
                title_data = json.loads(json_match.group())
                new_title = title_data.get("title", sources[0].title)
                new_tags = title_data.get("tags", [])
            else:
                new_title = f"合并知识 - {datetime.now().strftime('%Y-%m-%d')}"
                new_tags = []
            
            # Create new merged knowledge
            now = datetime.now()
            merged_knowledge = KnowledgeUnit(
                id=uuid6(),
                title=new_title,
                content=merged_content,
                tags=new_tags,
                source="merge",
                status=KnowledgeStatus.ACTIVE,
                score=0.0,
                created_at=now,
                updated_at=now,
            )
            
            # Add references to source knowledge
            merged_knowledge.relations = source_ids
            
            await self.storage.save_knowledge(merged_knowledge)
            
            # Update status
            status = self._load_status()
            status.last_merge_time = now
            self._save_status(status)
            
            # Delete merged sources if requested
            deleted_count = 0
            if auto_delete_duplicates:
                for sid in source_ids:
                    try:
                        await self.storage.delete_knowledge(UUID(sid))
                        deleted_count += 1
                    except Exception:
                        pass
            
            return MergeResult(
                merged_count=len(sources),
                deleted_count=deleted_count,
                created_knowledge=merged_knowledge,
                merged_ids=source_ids,
            )
            
        except Exception as e:
            logger.error(f"Merge failed: {e}")
            return MergeResult(error=str(e))

    def _build_merge_prompt(self, sources: List[KnowledgeUnit]) -> str:
        """Build prompt for LLM to merge knowledge"""
        items_text = []
        for i, k in enumerate(sources, 1):
            items_text.append(f"--- 知识 {i} ---\n标题：{k.title}\n{k.content[:500]}")
        
        return f"""请将以下多条知识内容进行整合和去重，生成一条结构清晰、内容完整的知识。

要求：
1. 保留所有关键信息，去除重复内容
2. 按照逻辑顺序组织内容
3. 适当添加连接词使文章流畅
4. 保持专业、准确的表达
5. 内容长度适中，一般不超过2000字

原始知识：
{'='*40}
{chr(10).join(items_text)}
{'='*40}

请直接输出整合后的知识内容，不要添加说明。"""

    async def deduplicate(self, threshold: float = 0.85) -> DeduplicationResult:
        """
        Find and remove duplicate knowledge items.
        
        Args:
            threshold: Similarity threshold for duplicates (0-1)
        
        Returns:
            DeduplicationResult with operation details
        """
        try:
            # Get all knowledge items
            all_knowledge, total = await self.storage.list_knowledge(
                page=1,
                page_size=1000
            )
            
            # Filter active items
            candidates = [
                k for k in all_knowledge
                if k.status in [KnowledgeStatus.DRAFT, KnowledgeStatus.ACTIVE]
            ]
            
            checked_count = len(candidates)
            duplicate_groups = []
            processed_ids = set()
            removed_count = 0
            
            for knowledge in candidates:
                if str(knowledge.id) in processed_ids:
                    continue
                
                # Find similar items
                similar = await self.find_similar_knowledge(
                    knowledge,
                    threshold=threshold,
                    limit=20
                )
                
                # Filter to only items above threshold
                duplicates = [
                    (k, score) for k, score in similar
                    if score >= threshold and str(k.id) not in processed_ids
                ]
                
                if len(duplicates) >= 1:  # Found at least one duplicate
                    group = {
                        "representative_id": str(knowledge.id),
                        "representative_title": knowledge.title,
                        "duplicates": [
                            {
                                "id": str(k.id),
                                "title": k.title,
                                "score": score,
                            }
                            for k, score in duplicates
                        ],
                    }
                    duplicate_groups.append(group)
                    
                    # Mark duplicates as processed (keep the first one)
                    for k, _ in duplicates:
                        processed_ids.add(str(k.id))
            
            # Update status
            status = self._load_status()
            status.last_dedup_time = datetime.now()
            self._save_status(status)
            
            return DeduplicationResult(
                checked_count=checked_count,
                duplicate_groups=duplicate_groups,
                removed_count=removed_count,
            )
            
        except Exception as e:
            logger.error(f"Deduplication failed: {e}")
            return DeduplicationResult(error=str(e))

    async def build_relations(self, knowledge_id: str, limit: int = 5) -> Dict[str, Any]:
        """
        Automatically build relations for a knowledge item.
        
        Args:
            knowledge_id: Knowledge ID to build relations for
            limit: Maximum number of relations to build
        
        Returns:
            Dict with relation details
        """
        try:
            knowledge = await self.storage.get_knowledge(UUID(knowledge_id))
            if not knowledge:
                return {"error": "Knowledge not found"}
            
            # Find similar knowledge
            similar = await self.find_similar_knowledge(knowledge, threshold=0.6, limit=limit)
            
            related_ids = [str(k.id) for k, _ in similar]
            
            # Update knowledge with new relations
            existing_relations = knowledge.relations or []
            new_relations = list(set(existing_relations + related_ids))
            
            await self.storage.update_knowledge(
                UUID(knowledge_id),
                {"relations": new_relations}
            )
            
            return {
                "knowledge_id": knowledge_id,
                "relations_added": related_ids,
                "total_relations": len(new_relations),
            }
            
        except Exception as e:
            logger.error(f"Build relations failed: {e}")
            return {"error": str(e)}

    async def generate_summary(
        self,
        summary_type: SummaryType,
        title: Optional[str] = None,
    ) -> SummaryResult:
        """
        Generate a periodic summary of knowledge.
        
        Args:
            summary_type: Type of summary (daily/weekly/monthly)
            title: Optional custom title for the summary
        
        Returns:
            SummaryResult with summary details
        """
        try:
            now = datetime.now()
            
            # Determine time range based on summary type
            if summary_type == SummaryType.DAILY:
                start_time = now - timedelta(days=1)
                default_title = f"每日总结 - {now.strftime('%Y-%m-%d')}"
                folder = "daily"
            elif summary_type == SummaryType.WEEKLY:
                start_time = now - timedelta(weeks=1)
                default_title = f"每周总结 - {now.strftime('%Y-W%U')}"
                folder = "weekly"
            else:  # MONTHLY
                start_time = now - timedelta(days=30)
                default_title = f"每月总结 - {now.strftime('%Y-%m')}"
                folder = "monthly"
            
            # Get knowledge created/updated in the time range
            all_knowledge, _ = await self.storage.list_knowledge(page=1, page_size=1000)
            
            relevant_knowledge = [
                k for k in all_knowledge
                if k.updated_at >= start_time
                and k.status in [KnowledgeStatus.DRAFT, KnowledgeStatus.ACTIVE]
            ]
            
            if not relevant_knowledge:
                return SummaryResult(
                    summary_type=summary_type,
                    content="该时间段内没有新知识",
                    knowledge_count=0,
                )
            
            # Build content for summary
            knowledge_summaries = []
            for k in relevant_knowledge[:50]:  # Limit to 50 items
                summary_text = k.summary or k.content[:200]
                knowledge_summaries.append(f"- **{k.title}**: {summary_text}")
            
            # Generate summary using LLM
            summary_prompt = f"""请根据以下知识条目生成一份{summary_type.value}总结报告。

要求：
1. 概述本{summary_type.value}新增/更新的主要内容主题
2. 归纳关键知识点和核心收获
3. 指出值得关注的重点内容
4. 保持简洁，500字以内
5. 结构清晰，使用Markdown格式

知识条目：
{chr(10).join(knowledge_summaries)}

请直接输出总结内容，不要添加说明。"""
            
            summary_content = await chat_completion(
                messages=[{"role": "user", "content": summary_prompt}]
            )
            
            # Create summary knowledge item
            summary_title = title or default_title
            related_ids = [str(k.id) for k in relevant_knowledge[:20]]
            
            summary_knowledge = KnowledgeUnit(
                id=uuid6(),
                title=summary_title,
                content=summary_content,
                summary=summary_content[:200] if len(summary_content) > 200 else summary_content,
                tags=[summary_type.value, "summary", "auto-generated"],
                source="summary",
                source_refs=related_ids,
                status=KnowledgeStatus.ACTIVE,
                score=0.5,
                created_at=now,
                updated_at=now,
            )
            
            # Save to summaries folder
            folder_path = os.path.join(settings.knowledge_base_path, "summaries", folder)
            file_path = os.path.join(folder_path, f"{summary_knowledge.id}.md")
            
            import frontmatter
            metadata = {
                "id": str(summary_knowledge.id),
                "title": summary_knowledge.title,
                "summary": summary_knowledge.summary,
                "tags": summary_knowledge.tags,
                "category": "summary",
                "source": summary_knowledge.source,
                "created_at": summary_knowledge.created_at.isoformat(),
                "updated_at": summary_knowledge.updated_at.isoformat(),
                "status": summary_knowledge.status.value,
            }
            post = frontmatter.Post(summary_knowledge.content, **metadata)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._write_frontmatter,
                file_path,
                post
            )
            
            # Update status
            status = self._load_status()
            status.last_summary_time = now
            self._save_status(status)
            
            return SummaryResult(
                summary_id=str(summary_knowledge.id),
                summary_type=summary_type,
                content=summary_content,
                knowledge_count=len(relevant_knowledge),
            )
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return SummaryResult(error=str(e))

    def _write_frontmatter(self, file_path: str, post: "frontmatter.Post"):
        """Write frontmatter to file"""
        import frontmatter
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    async def run_integration(self, include_summary: bool = True) -> Dict[str, Any]:
        """
        Run full memory integration process.
        
        Args:
            include_summary: Whether to generate daily summary after integration
        
        Returns:
            Dict with integration results
        """
        results = {
            "deduplication": None,
            "relation_building": None,
            "summary": None,
        }
        
        # Step 1: Deduplication
        logger.info("Starting deduplication...")
        dedup_result = await self.deduplicate(threshold=0.85)
        results["deduplication"] = {
            "checked_count": dedup_result.checked_count,
            "duplicate_groups": len(dedup_result.duplicate_groups),
            "error": dedup_result.error,
        }
        
        # Step 2: Build relations for active knowledge
        logger.info("Building knowledge relations...")
        all_knowledge, _ = await self.storage.list_knowledge(
            category="permanent_notes",
            page=1,
            page_size=100
        )
        
        relations_built = 0
        for k in all_knowledge[:20]:  # Limit to avoid API rate limits
            result = await self.build_relations(str(k.id), limit=3)
            if "relations_added" in result:
                relations_built += len(result["relations_added"])
        
        results["relation_building"] = {
            "knowledge_processed": min(20, len(all_knowledge)),
            "relations_built": relations_built,
        }
        
        # Step 3: Generate daily summary
        if include_summary:
            logger.info("Generating daily summary...")
            summary_result = await self.generate_summary(SummaryType.DAILY)
            results["summary"] = {
                "summary_id": summary_result.summary_id,
                "knowledge_count": summary_result.knowledge_count,
                "error": summary_result.error,
            }
        
        return results
