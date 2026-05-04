from fastapi import APIRouter, Body
from models.schemas import BaseResponse, ContentCollectRequest
from services.content_service import ContentService

router = APIRouter()
content_service = ContentService()

@router.post("/content/collect", response_model=BaseResponse)
async def collect_content(request: ContentCollectRequest = Body(...)):
    knowledge = await content_service.collect(request)
    return BaseResponse(data=knowledge.dict())