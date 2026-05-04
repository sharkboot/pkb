import asyncio
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from uuid6 import uuid6
from datetime import datetime
from storage.markdown_storage import MarkdownStorage
from models.schemas import Task, TaskCreateRequest
from models.enums import TaskType
from models.exceptions import ResourceNotFoundException, TaskExecuteException
from llm.provider import chat_completion, create_embedding, chat_completion_with_images
from core.config import settings

logger = logging.getLogger(__name__)

class TaskService:
    def __init__(self):
        self.storage = MarkdownStorage()

    async def create_task(self, request: TaskCreateRequest) -> Task:
        now = datetime.now()
        task = Task(
            id=uuid6(),
            task_type=request.task_type,
            target_id=request.target_id,
            params=request.params or {},
            status="pending",
            result=None,
            created_at=now,
            updated_at=now,
        )
        
        await self.storage.save_task(task)
        asyncio.create_task(self._execute_task(task.id))
        return task

    async def _execute_task(self, task_id: UUID):
        logger.info(f"开始执行任务: {task_id}")
        task = await self.storage.get_task(task_id)
        if not task:
            logger.warning(f"任务 {task_id} 不存在")
            return
        
        await self.storage.update_task(task_id, {"status": "running"})
        logger.info(f"任务 {task_id} 状态更新为 running")
        
        try:
            result = await self._process_task(task)
            await self.storage.update_task(task_id, {"status": "completed", "result": result})
            logger.info(f"任务 {task_id} 执行完成: {result}")
        except Exception as e:
            await self.storage.update_task(task_id, {"status": "failed", "result": {"error": str(e)}})
            logger.error(f"任务 {task_id} 执行失败: {str(e)}")

    async def _process_task(self, task: Task) -> Dict[str, Any]:
        task_type = task.task_type
        
        if task_type == TaskType.OCR:
            return await self._process_ocr(task)
        elif task_type == TaskType.SUMMARY:
            return await self._process_summary(task)
        elif task_type == TaskType.MERGE:
            return await self._process_merge(task)
        elif task_type == TaskType.ARCHIVE:
            return await self._process_archive(task)
        elif task_type == TaskType.VECTOR_INDEX:
            return await self._process_vector_index(task)
        elif task_type == TaskType.DEDUPLICATION:
            return await self._process_deduplication(task)
        else:
            raise TaskExecuteException(f"未知任务类型: {task_type}")

    async def _get_knowledge_content(self, target_id: str) -> Optional[str]:
        try:
            knowledge_id = UUID(target_id)
            knowledge = await self.storage.get_knowledge(knowledge_id)
            return knowledge.content if knowledge else None
        except Exception:
            return None

    async def _process_ocr(self, task: Task) -> Dict[str, Any]:
        logger.info(f"开始处理 OCR 任务: {task.id}")
        content = await self._get_knowledge_content(task.target_id)

        if not content:
            return {"message": "未找到内容", "target_id": task.target_id}

        # 从 markdown 内容中提取图片 URL
        import re
        image_urls = re.findall(r'!\[.*?\]\((.*?)\)', content)

        try:
            if image_urls:
                prompt = "请分析这些图片中的内容，提取并整理所有文字信息："
                messages = [{"role": "user", "content": prompt}]
                ocr_result = await chat_completion_with_images(
                    messages=messages,
                    image_urls=image_urls,
                )
            else:
                ocr_result = await chat_completion(
                    messages=[{"role": "user", "content": "请分析以下内容：\n\n" + content}]
                )

            # 调用 LLM 生成摘要
            summary_prompt = f"请为以下内容生成一个简洁的摘要，不超过100字，直接输出摘要文本，不要使用markdown格式：\n\n{ocr_result}"
            summary = await chat_completion(
                messages=[{"role": "user", "content": summary_prompt}]
            )

            # 保留原始图片，追加 OCR 结果
            ocr_content = content + "\n\n---\n## OCR 识别结果\n\n" + ocr_result

            # 更新知识内容（保留图片 + OCR 结果）
            await self.storage.update_knowledge(
                UUID(task.target_id),
                {
                    "content": ocr_content,
                    "summary": summary,
                    "source": "OCR",
                }
            )
            logger.info(f"OCR 任务完成: {task.id}")
            return {
                "message": "OCR任务已完成",
                "target_id": task.target_id,
                "ocr_result": ocr_result,
                "summary": summary,
                "content_length": len(content),
                "images_count": len(image_urls),
            }
        except Exception as e:
            logger.error(f"OCR 任务失败: {str(e)}")
            return {
                "message": "OCR任务处理失败",
                "target_id": task.target_id,
                "error": str(e)
            }

    async def _process_summary(self, task: Task) -> Dict[str, Any]:
        content = await self._get_knowledge_content(task.target_id)
        if not content:
            return {"message": "未找到内容", "target_id": task.target_id}

        mode = task.params.get("mode", "daily")

        # 提取图片 URL
        import re
        image_urls = re.findall(r'!\[.*?\]\((.*?)\)', content)
        text_only = re.sub(r'!\[.*?\]\(.*?\)', '', content).strip()

        try:
            if image_urls:
                # 图片输入：先提取图片内容，再用模型总结
                extract_prompt = "请分析这些图片，提取其中的文字和关键信息："
                image_content = await chat_completion_with_images(
                    messages=[{"role": "user", "content": extract_prompt}],
                    image_urls=image_urls,
                )
                full_content = f"{text_only}\n\n图片内容：\n{image_content}" if text_only else f"图片内容：\n{image_content}"
            else:
                # 纯文本输入：直接总结
                full_content = text_only

            summary_prompt = f"请为以下内容生成一个简洁的总结，不超过100字，直接输出总结文本，不要使用markdown格式：\n\n{full_content}"
            summary = await chat_completion(messages=[{"role": "user", "content": summary_prompt}])

            await self.storage.update_knowledge(UUID(task.target_id), {"summary": summary})
            return {"message": f"{mode}总结任务已完成", "target_id": task.target_id, "summary": summary}
        except Exception as e:
            logger.error(f"总结任务失败: {str(e)}")
            return {"message": f"总结任务失败: {str(e)}", "target_id": task.target_id}

    async def _process_merge(self, task: Task) -> Dict[str, Any]:
        return {"message": "知识合并任务已处理", "target_id": task.target_id}

    async def _process_archive(self, task: Task) -> Dict[str, Any]:
        content = await self._get_knowledge_content(task.target_id)
        if not content:
            return {"message": "未找到内容", "target_id": task.target_id}
        
        prompt = f"判断以下内容是否应该归档，并给出归档类别建议：\n\n{content}"
        
        try:
            advice = await chat_completion(messages=[{"role": "user", "content": prompt}])
            return {"message": "归档建议已生成", "target_id": task.target_id, "advice": advice}
        except Exception as e:
            logger.error(f"归档任务失败: {str(e)}")
            return {"message": f"归档任务失败: {str(e)}", "target_id": task.target_id}

    async def _process_vector_index(self, task: Task) -> Dict[str, Any]:
        content = await self._get_knowledge_content(task.target_id)
        if not content:
            return {"message": "未找到内容", "target_id": task.target_id}
        
        try:
            embedding = await create_embedding(text=content[:1000])
            return {"message": "向量索引已生成", "target_id": task.target_id, "embedding_dim": len(embedding)}
        except Exception as e:
            logger.error(f"向量索引任务失败: {str(e)}")
            return {"message": f"向量索引任务失败: {str(e)}", "target_id": task.target_id}

    async def _process_deduplication(self, task: Task) -> Dict[str, Any]:
        return {"message": "去重处理任务已处理", "target_id": task.target_id}

    async def get_task(self, task_id: UUID) -> Task:
        task = await self.storage.get_task(task_id)
        if not task:
            raise ResourceNotFoundException(f"任务 {task_id} 不存在")
        return task

    async def list_tasks(self) -> List[Task]:
        return await self.storage.list_tasks()