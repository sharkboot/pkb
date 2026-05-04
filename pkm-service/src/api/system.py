from fastapi import APIRouter, Body
from models.schemas import BaseResponse, SystemConfig
from services.system_service import SystemService

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