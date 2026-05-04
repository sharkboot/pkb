from fastapi import APIRouter
from api.content import router as content_router
from api.sessions import router as sessions_router
from api.knowledge import router as knowledge_router
from api.ai import router as ai_router
from api.files import router as files_router
from api.categories import router as categories_router
from api.system import router as system_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(content_router)
api_router.include_router(sessions_router)
api_router.include_router(knowledge_router)
api_router.include_router(ai_router)
api_router.include_router(files_router)
api_router.include_router(categories_router)
api_router.include_router(system_router)