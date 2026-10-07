from fastapi import APIRouter, File, UploadFile, Body, Query
from uuid import UUID
from models.schemas import BaseResponse
from services.file_service import FileService

router = APIRouter()
file_service = FileService()

@router.get("/files/md/{knowledge_id}", response_model=BaseResponse)
async def get_markdown(knowledge_id: UUID):
    content = file_service.get_markdown_content(knowledge_id)
    return BaseResponse(data={"content": content})

@router.post("/files/md/merge", response_model=BaseResponse)
async def merge_markdown():
    result = await file_service.merge_fragments()
    return BaseResponse(data=result)

@router.post("/files/export", response_model=BaseResponse)
async def export_knowledge_base():
    path = await file_service.export_knowledge_base()
    return BaseResponse(data={"path": path})

@router.post("/upload/image", response_model=BaseResponse)
async def upload_image(
    file: UploadFile = File(...),
    folder: str = Query(None),
):
    result = await file_service.upload_image(file, folder)
    return BaseResponse(data=result.dict())

@router.post("/files/import/markdown", response_model=BaseResponse)
async def import_markdown(
    file: UploadFile = File(...),
):
    """导入单个 Markdown 文件并创建知识单元"""
    result = await file_service.import_markdown(file)
    return BaseResponse(data=result.dict())


@router.post("/files/import/markdown/batch", response_model=BaseResponse)
async def import_markdown_batch(
    file: UploadFile = File(...),
):
    """批量导入 zip 压缩包中的 Markdown 文件。

    支持：
    - 递归扫描所有 .md 文件
    - 子目录自动映射到 category
    - 相同内容自动去重
    - 返回汇总报告（imported / skipped / errors）
    """
    result = await file_service.import_markdown_batch(file)
    return BaseResponse(data=result)