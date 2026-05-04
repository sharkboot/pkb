from fastapi import APIRouter, Body, Path
from uuid import UUID
from models.schemas import BaseResponse, CategoryCreateRequest
from services.category_service import CategoryService

router = APIRouter()
category_service = CategoryService()

@router.get("/categories", response_model=BaseResponse)
async def list_categories():
    categories = await category_service.list_categories()
    return BaseResponse(data=[c.dict() for c in categories])

@router.post("/categories", response_model=BaseResponse)
async def create_category(request: CategoryCreateRequest = Body(...)):
    category = await category_service.create_category(request)
    return BaseResponse(data=category.dict())

@router.delete("/categories/{category_id}", response_model=BaseResponse)
async def delete_category(category_id: UUID = Path(...)):
    success = await category_service.delete_category(category_id)
    return BaseResponse(data={"success": success})