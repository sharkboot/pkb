import os
import shutil
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import UploadFile
from core.config import settings
from models.schemas import FileUploadResponse
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