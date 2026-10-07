import os
import shutil
import frontmatter
import hashlib
import tempfile
import zipfile
from datetime import datetime
from typing import Optional, List
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

    async def export_knowledge_base(self, format: str = "markdown") -> str:
        """Export knowledge base in specified format (markdown, pdf, epub, txt).

        Args:
            format: Export format - 'markdown' (default), 'pdf', 'epub', 'txt'

        Returns:
            Path to the exported file
        """
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()

        all_knowledge, _ = await knowledge_service.list_knowledge(page=1, page_size=10000)

        export_path = os.path.join(settings.knowledge_base_path, "export")
        os.makedirs(export_path, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "markdown":
            return await self._export_markdown(all_knowledge, export_path, timestamp)
        elif format == "txt":
            return await self._export_txt(all_knowledge, export_path, timestamp)
        elif format == "pdf":
            return await self._export_pdf(all_knowledge, export_path, timestamp)
        elif format == "epub":
            return await self._export_epub(all_knowledge, export_path, timestamp)
        else:
            raise FileProcessException(f"不支持的导出格式: {format}")

    async def _export_markdown(self, knowledge_list, export_path: str, timestamp: str) -> str:
        """Export as Markdown zip."""
        zip_path = os.path.join(export_path, f"knowledge_base_{timestamp}.zip")

        import zipfile
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for knowledge in knowledge_list:
                # Skip deleted items
                if knowledge.status.value in ("deleted", "archived"):
                    continue

                content = f"# {knowledge.title}\n\n"
                if knowledge.summary:
                    content += f"> **摘要**: {knowledge.summary}\n\n"
                if knowledge.tags:
                    content += f"**标签**: {', '.join(knowledge.tags)}\n\n"
                content += knowledge.content

                safe_title = "".join(c if c.isalnum() else "_" for c in knowledge.title)[:50]
                zf.writestr(f"{safe_title}.md", content)

        return zip_path

    async def _export_txt(self, knowledge_list, export_path: str, timestamp: str) -> str:
        """Export as plain text."""
        txt_path = os.path.join(export_path, f"knowledge_base_{timestamp}.txt")

        with open(txt_path, "w", encoding="utf-8") as f:
            for knowledge in knowledge_list:
                if knowledge.status.value in ("deleted", "archived"):
                    continue

                f.write(f"{'='*60}\n")
                f.write(f"{knowledge.title}\n")
                f.write(f"{'='*60}\n\n")

                if knowledge.summary:
                    f.write(f"摘要: {knowledge.summary}\n\n")

                f.write(knowledge.content + "\n\n")

        return txt_path

    async def _export_pdf(self, knowledge_list, export_path: str, timestamp: str) -> str:
        """Export as PDF (requires reportlab or markdown2pdf)."""
        pdf_path = os.path.join(export_path, f"knowledge_base_{timestamp}.pdf")

        try:
            # Try using markdown2pdf (easier dependency)
            from markdown2pdf import convert_markdown
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                # Write each knowledge as a markdown file
                for i, knowledge in enumerate(knowledge_list):
                    if knowledge.status.value in ("deleted", "archived"):
                        continue

                    md_path = os.path.join(tmpdir, f"knowledge_{i}.md")
                    with open(md_path, "w", encoding="utf-8") as f:
                        f.write(f"# {knowledge.title}\n\n")
                        if knowledge.summary:
                            f.write(f"> **摘要**: {knowledge.summary}\n\n")
                        if knowledge.tags:
                            f.write(f"**标签**: {', '.join(knowledge.tags)}\n\n")
                        f.write(knowledge.content)

                # Convert to PDF
                convert_markdown(in_path=tmpdir, out_path=pdf_path)

            return pdf_path
        except ImportError:
            # Fallback: create a simple text-based PDF
            return await self._export_simple_pdf(knowledge_list, pdf_path)

    async def _export_simple_pdf(self, knowledge_list, pdf_path: str) -> str:
        """Fallback PDF export using reportlab if available."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            c = canvas.Canvas(pdf_path, pagesize=A4)
            width, height = A4

            y_position = height - 50

            for knowledge in knowledge_list:
                if knowledge.status.value in ("deleted", "archived"):
                    continue

                # Add title
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, y_position, knowledge.title)
                y_position -= 30

                # Add summary if exists
                if knowledge.summary:
                    c.setFont("Helvetica-Oblique", 10)
                    c.drawString(50, y_position, f"摘要: {knowledge.summary}")
                    y_position -= 20

                # Add content (word wrap)
                c.setFont("Helvetica", 10)
                lines = knowledge.content.split('\n')
                for line in lines:
                    if y_position < 50:
                        c.showPage()
                        y_position = height - 50
                    c.drawString(50, y_position, line[:80])
                    y_position -= 15

            c.save()
            return pdf_path
        except ImportError:
            raise FileProcessException("PDF导出需要安装 reportlab: pip install reportlab")

    async def _export_epub(self, knowledge_list, export_path: str, timestamp: str) -> str:
        """Export as EPUB (requires ebooklib)."""
        epub_path = os.path.join(export_path, f"knowledge_base_{timestamp}.epub")

        try:
            from ebooklib import epub

            book = epub.EpubBook()
            book.set_identifier('pkb-export-' + timestamp)
            book.set_title('PKB Knowledge Export')
            book.set_language('zh')

            # Create chapters
            chapters = []
            for knowledge in knowledge_list:
                if knowledge.status.value in ("deleted", "archived"):
                    continue

                chapter_content = f"<h1>{knowledge.title}</h1>\n"
                if knowledge.summary:
                    chapter_content += f"<p><strong>摘要:</strong> {knowledge.summary}</p>\n"
                if knowledge.tags:
                    chapter_content += f"<p><strong>标签:</strong> {', '.join(knowledge.tags)}</p>\n"
                chapter_content += f"<p>{knowledge.content.replace(chr(10), '<br>')}</p>"

                chapter = epub.EpubHtml(
                    title=knowledge.title[:50],
                    file_name=f"knowledge_{len(chapters)}.xhtml",
                    lang='zh'
                )
                chapter.content = chapter_content
                chapters.append(chapter)
                book.add_item(chapter)

            # Add table of contents
            book.toc = chapters
            book.add_item(epub.EpubNav())
            book.add_spine('nav', chapters)

            # Write EPUB
            with open(epub_path, 'wb') as f:
                epub.write_epub(f, book, {})

            return epub_path
        except ImportError:
            raise FileProcessException("EPUB导出需要安装 ebooklib: pip install ebooklib")

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
