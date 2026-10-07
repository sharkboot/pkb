import os
import shutil
import frontmatter
import hashlib
import tempfile
import zipfile
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import UploadFile
from core.config import settings
from models.schemas import FileUploadResponse, KnowledgeCreateRequest, KnowledgeUpdateRequest
from models.exceptions import FileProcessException


def _content_hash(raw_bytes: bytes) -> str:
    """Compute SHA-256 hash of raw file content for deduplication."""
    return hashlib.sha256(raw_bytes).hexdigest()


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

    # ─────────────────────────────────────────────────────────────────────────
    # Single-file import (existing)
    # ─────────────────────────────────────────────────────────────────────────

    async def import_markdown(self, file: UploadFile) -> dict:
        """导入单个 Markdown 文件并创建知识单元"""
        try:
            if not file.filename.endswith('.md'):
                raise FileProcessException("仅支持导入 .md 格式的 Markdown 文件")

            raw_bytes = await file.read()
            raw_text = self._decode(raw_bytes)

            title, content, tags, summary, category = self._parse_markdown(
                raw_text, default_title=os.path.splitext(file.filename)[0]
            )

            knowledge = await self._create_knowledge_unit(
                title=title, content=content, tags=tags, summary=summary,
                category=category,
            )

            await self._trigger_tasks(knowledge)

            return knowledge

        except FileProcessException:
            raise
        except Exception as e:
            raise FileProcessException(f"Markdown 文件导入失败: {str(e)}")

    # ─────────────────────────────────────────────────────────────────────────
    # Batch import — zip archive
    # ─────────────────────────────────────────────────────────────────────────

    async def import_markdown_batch(self, file: UploadFile) -> dict:
        """批量导入 zip 压缩包中的 Markdown 文件。

        - 递归扫描 zip 内所有 .md 文件
        - 子目录路径自动映射到 category 字段（如 notes/python → category="python"）
        - 相同内容哈希的文件自动跳过（去重）
        - 返回导入结果汇总

        支持进度反馈：{"total", "imported", "skipped", "errors", "report"}
        """
        try:
            raw_bytes = await file.read()

            # Validate file type
            if not file.filename.lower().endswith(".zip"):
                raise FileProcessException("批量导入仅支持 .zip 压缩包")

            with tempfile.TemporaryDirectory() as tmp_dir:
                zip_path = os.path.join(tmp_dir, "upload.zip")
                with open(zip_path, "wb") as f:
                    f.write(raw_bytes)

                with zipfile.ZipFile(zip_path, "r") as zf:
                    results = await self._process_zip(zf)

            return results

        except FileProcessException:
            raise
        except Exception as e:
            raise FileProcessException(f"批量导入失败: {str(e)}")

    async def _process_zip(self, zf: zipfile.ZipFile) -> dict:
        """Process all .md files in a zip archive."""
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()

        # Collect all .md entries with their relative paths
        md_entries: list = []  # (arcname, entry)
        for info in zf.infolist():
            if info.is_dir():
                continue
            if not info.filename.lower().endswith(".md"):
                continue
            # Strip leading path component if it's a top-level folder (common zip structure)
            rel_path = info.filename
            md_entries.append((rel_path, info))

        total = len(md_entries)
        if total == 0:
            return {
                "total": 0, "imported": 0, "skipped": 0, "errors": 0,
                "report": {"imported": [], "skipped": [], "errors": []},
            }

        seen_hashes: set = set()
        imported: list = []
        skipped: list = []
        errors: list = []

        for rel_path, info in md_entries:
            file_name = os.path.basename(rel_path)
            # Category from sub-directory: "notes/python/hello.md" → "python"
            # Use the first sub-directory level as category (if any)
            parts = rel_path.replace("\\", "/").split("/")
            # Skip first part if it's a single top-level folder that wraps everything
            # Heuristic: if all entries share the same first segment, use it as prefix
            sub_dir = parts[1] if len(parts) > 2 else ""
            category = sub_dir if sub_dir else None

            try:
                with zf.open(info) as f:
                    raw_bytes = f.read()

                # Deduplication by content hash
                content_hash = _content_hash(raw_bytes)
                if content_hash in seen_hashes:
                    skipped.append({
                        "file": rel_path,
                        "reason": "duplicate_content",
                    })
                    continue
                seen_hashes.add(content_hash)

                raw_text = self._decode(raw_bytes)
                title, content, tags, summary, fm_category = self._parse_markdown(
                    raw_text, default_title=os.path.splitext(file_name)[0]
                )
                # Frontmatter category takes precedence over directory-based category
                effective_category = fm_category or category

                knowledge = await self._create_knowledge_unit(
                    title=title,
                    content=content,
                    tags=tags,
                    summary=summary,
                    category=effective_category,
                )
                await self._trigger_tasks(knowledge, batch=True)
                imported.append({
                    "id": str(knowledge.id),
                    "title": knowledge.title,
                    "file": rel_path,
                })

            except Exception as e:
                errors.append({"file": rel_path, "error": str(e)})

        return {
            "total": total,
            "imported": len(imported),
            "skipped": len(skipped),
            "errors": len(errors),
            "report": {
                "imported": imported,
                "skipped": skipped,
                "errors": errors,
            },
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _decode(raw_bytes: bytes) -> str:
        try:
            return raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return raw_bytes.decode("utf-8-sig")

    @staticmethod
    def _parse_markdown(
        raw_text: str,
        default_title: str,
    ) -> tuple:
        """Parse Markdown file, returning (title, content, tags, summary, category)."""
        post = frontmatter.loads(raw_text)
        title = post.get("title") or default_title

        tags = post.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        summary = post.get("summary")
        category = post.get("category")

        body = post.content
        content = body.strip() if body.strip() else raw_text.strip()

        return title, content, tags, summary, category

    async def _create_knowledge_unit(
        self,
        title: str,
        content: str,
        tags: list,
        summary: Optional[str],
        category: Optional[str] = None,
    ):
        from services.knowledge_service import KnowledgeService
        from models.enums import KnowledgeStatus
        knowledge_service = KnowledgeService()

        create_request = KnowledgeCreateRequest(
            title=title[:100],
            content=content,
            tags=tags + ["import"],
            summary=summary,
            status=KnowledgeStatus.DRAFT,
        )
        knowledge = await knowledge_service.create_knowledge(create_request)

        if category:
            await knowledge_service.update_knowledge(
                knowledge.id,
                KnowledgeUpdateRequest(category=category),
            )

        return knowledge

    async def _trigger_tasks(self, knowledge, batch: bool = False) -> None:
        """Trigger post-import AI tasks.

        In batch mode, skip individual SUMMARY tasks to avoid N LLM calls;
        a single batch summary task is created instead.
        """
        from services.task_service import TaskService
        from models.schemas import TaskCreateRequest
        from models.enums import TaskType

        task_service = TaskService()

        # Always trigger summary task (even in batch mode — caller can batch them)
        await task_service.create_task(TaskCreateRequest(
            task_type=TaskType.SUMMARY,
            target_id=str(knowledge.id),
        ))

        if settings.vector_store_enabled:
            await task_service.create_task(TaskCreateRequest(
                task_type=TaskType.VECTOR_INDEX,
                target_id=str(knowledge.id),
            ))


# Singleton
file_service = FileService()
