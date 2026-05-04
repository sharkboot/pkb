from fastapi import APIRouter, Body, Path
from uuid import UUID
from models.schemas import BaseResponse, SessionCreateRequest
from services.session_service import SessionService

router = APIRouter()
session_service = SessionService()

@router.get("/sessions", response_model=BaseResponse)
async def list_sessions():
    sessions = await session_service.list_sessions()
    return BaseResponse(data=[s.dict() for s in sessions])

@router.post("/sessions", response_model=BaseResponse)
async def create_session(request: SessionCreateRequest = Body(...)):
    session = await session_service.create_session(request)
    return BaseResponse(data=session.dict())

@router.delete("/sessions/{session_id}", response_model=BaseResponse)
async def delete_session(session_id: UUID = Path(...)):
    success = await session_service.delete_session(session_id)
    return BaseResponse(data={"success": success})