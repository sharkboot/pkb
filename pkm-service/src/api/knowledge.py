from fastapi import APIRouter, Body, Path, Query
from uuid import UUID
from models.schemas import BaseResponse, KnowledgeCreateRequest, KnowledgeUpdateRequest
from services.knowledge_service import KnowledgeService

router = APIRouter()
knowledge_service = KnowledgeService()

@router.get("/knowledge", response_model=BaseResponse)
async def list_knowledge(
    category: str = Query(None),
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    knowledge_list, total = await knowledge_service.list_knowledge(category, keyword, page, page_size)
    return BaseResponse(data={
        "list": [k.dict() for k in knowledge_list],
        "total": total,
        "page": page,
        "pageSize": page_size,
    })

@router.post("/knowledge", response_model=BaseResponse)
async def create_knowledge(request: KnowledgeCreateRequest = Body(...)):
    knowledge = await knowledge_service.create_knowledge(request)
    return BaseResponse(data=knowledge.dict())

@router.get("/knowledge/{knowledge_id}", response_model=BaseResponse)
async def get_knowledge(knowledge_id: UUID = Path(...)):
    knowledge = await knowledge_service.get_knowledge(knowledge_id)
    return BaseResponse(data=knowledge.dict())

@router.put("/knowledge/{knowledge_id}", response_model=BaseResponse)
async def update_knowledge(
    knowledge_id: UUID = Path(...),
    request: KnowledgeUpdateRequest = Body(...),
):
    knowledge = await knowledge_service.update_knowledge(knowledge_id, request)
    return BaseResponse(data=knowledge.dict())

@router.delete("/knowledge/{knowledge_id}", response_model=BaseResponse)
async def delete_knowledge(knowledge_id: UUID = Path(...)):
    success = await knowledge_service.delete_knowledge(knowledge_id)
    return BaseResponse(data={"success": success})

@router.post("/knowledge/{knowledge_id}/star", response_model=BaseResponse)
async def star_knowledge(knowledge_id: UUID = Path(...)):
    knowledge = await knowledge_service.star_knowledge(knowledge_id)
    return BaseResponse(data=knowledge.dict())

@router.post("/knowledge/{knowledge_id}/restore", response_model=BaseResponse)
async def restore_knowledge(knowledge_id: UUID = Path(...)):
    knowledge = await knowledge_service.restore_knowledge(knowledge_id)
    return BaseResponse(data=knowledge.dict())

@router.delete("/knowledge/{knowledge_id}/permanent", response_model=BaseResponse)
async def permanent_delete(knowledge_id: UUID = Path(...)):
    success = await knowledge_service.permanent_delete(knowledge_id)
    return BaseResponse(data={"success": success})