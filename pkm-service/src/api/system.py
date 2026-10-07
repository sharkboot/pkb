from fastapi import APIRouter, Body
from models.schemas import BaseResponse, SystemConfig
from services.system_service import SystemService
from storage.embedding_cache import embedding_cache

router = APIRouter()
system_service = SystemService()

@router.get("/system/config", response_model=BaseResponse)
async def get_config():
    config = system_service.get_config()
    return BaseResponse(data=config.dict())

@router.put("/system/config", response_model=BaseResponse)
async def update_config(config: SystemConfig = Body(...)):
    updated = system_service.update_config(config)
    return BaseResponse(data=updated.dict())

@router.get("/system/embedding-cache", response_model=BaseResponse)
async def embedding_cache_status():
    """Get embedding cache statistics (entries, hit rate)."""
    stats = embedding_cache.stats()
    return BaseResponse(data=stats)

@router.post("/system/embedding-cache/clear", response_model=BaseResponse)
async def clear_embedding_cache():
    """Clear the embedding cache and reset counters."""
    embedding_cache.clear()
    return BaseResponse(data={"message": "Embedding cache cleared"})