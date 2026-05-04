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