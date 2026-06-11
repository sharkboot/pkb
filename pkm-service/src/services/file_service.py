import os
import shutil
import frontmatter
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import UploadFile
from core.config import settings
from models.schemas import FileUploadResponse, KnowledgeCreateRequest, KnowledgeUpdateRequest
from models.exceptions import FileProcessException

class FileService:
    def __init__(self):
        self.upload_dir = os.path.join(settings.knowledge_base_path, "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

    async def upload_image(self, file: UploadFile, folder: Optional[str] = None) -> FileUploadResponse:
        try:
            if folder:
                target_dir = os.path.join(self.upload_dir, folder)
            else:
                target_dir = self.upload_dir
            
            os.makedirs(target_dir, exist_ok=True)
            
            file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
            filename = f"{UUID(int=0).hex[:16]}_{file.filename}"
            file_path = os.path.join(target_dir, filename)
            
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            return FileUploadResponse(
                url=f"/api/v1/files/{filename}",
                filename=filename,
                folder=folder,
            )
        except Exception as e:
            raise FileProcessException(f"文件上传失败: {str(e)}")

    async def export_knowledge_base(self) -> str:
        try:
            export_path = os.path.join(settings.knowledge_base_path, "export")
            os.makedirs(export_path, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = os.path.join(export_path, f"knowledge_base_{timestamp}.zip")
            
            shutil.make_archive(zip_path.replace(".zip", ""), "zip", settings.knowledge_base_path)
            
            return zip_path
        except Exception as e:
            raise FileProcessException(f"导出失败: {str(e)}")

    def get_markdown_content(self, knowledge_id: UUID) -> Optional[str]:
        from services.knowledge_service import KnowledgeService
        service = KnowledgeService()
        try:
            knowledge = service.get_knowledge(knowledge_id)
            return knowledge.content
        except Exception:
            return None

    async def merge_fragments(self) -> dict:
        return {"message": "碎片内容合并完成"}

    async def import_markdown(self, file: UploadFile) -> dict:
        """导入 Markdown 文件并创建知识单元"""
        try:
            # 1. 验证文件扩展名
            if not file.filename.endswith('.md'):
                raise FileProcessException("仅支持导入 .md 格式的 Markdown 文件")

            # 2. 读取并解码文件内容
            content_bytes = await file.read()
            try:
                raw_text = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                raw_text = content_bytes.decode('utf-8-sig')  # 处理 BOM

            # 3. 解析 frontmatter
            post = frontmatter.loads(raw_text)

            # 4. 从 frontmatter 提取元数据，带默认值
            title = post.get('title') or os.path.splitext(file.filename)[0]
            tags = post.get('tags', [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',')]
            summary = post.get('summary')
            category = post.get('category')

            # 5. 正文内容是 post.content（frontmatter 块之后的所有内容）
            body = post.content

            # 6. 构建 markdown 内容，保留原始结构
            content = body.strip() if body.strip() else raw_text.strip()

            # 7. 通过 KnowledgeService 创建知识
            from services.knowledge_service import KnowledgeService
            knowledge_service = KnowledgeService()

            create_request = KnowledgeCreateRequest(
                title=title[:100],
                content=content,
                tags=tags + ['import'],  # 添加 'import' 标签标记来源
                summary=summary,
            )
            knowledge = await knowledge_service.create_knowledge(create_request)

            # 8. 如果 frontmatter 中有 category，更新分类
            if category:
                await knowledge_service.update_knowledge(
                    knowledge.id,
                    KnowledgeUpdateRequest(category=category)
                )

            # 9. 触发 AI 处理任务
            from services.task_service import TaskService
            from models.schemas import TaskCreateRequest
            from models.enums import TaskType
            task_service = TaskService()

            # 始终触发摘要生成任务
            await task_service.create_task(TaskCreateRequest(
                task_type=TaskType.SUMMARY,
                target_id=str(knowledge.id),
            ))

            # 如果配置了向量存储，触发向量索引任务
            if hasattr(settings, 'vector_store_enabled') and settings.vector_store_enabled:
                await task_service.create_task(TaskCreateRequest(
                    task_type=TaskType.VECTOR_INDEX,
                    target_id=str(knowledge.id),
                ))

            return knowledge

        except FileProcessException:
            raise
        except Exception as e:
            raise FileProcessException(f"Markdown 文件导入失败: {str(e)}")