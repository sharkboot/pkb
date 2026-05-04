from fastapi import APIRouter, Body, Path
from uuid import UUID
from models.schemas import BaseResponse, TaskCreateRequest
from services.task_service import TaskService

router = APIRouter()
task_service = TaskService()

@router.post("/ai/tasks", response_model=BaseResponse)
async def create_task(request: TaskCreateRequest = Body(...)):
    task = await task_service.create_task(request)
    return BaseResponse(data=task.dict())

@router.get("/ai/tasks/{task_id}", response_model=BaseResponse)
async def get_task(task_id: UUID = Path(...)):
    task = await task_service.get_task(task_id)
    return BaseResponse(data=task.dict())

@router.get("/ai/tasks", response_model=BaseResponse)
async def list_tasks():
    tasks = await task_service.list_tasks()
    return BaseResponse(data=[t.dict() for t in tasks])