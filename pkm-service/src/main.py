from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from api import api_router
from core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PKM 知识管理系统",
    version="v2.0.0",
    description="基于 Python + LLM + Markdown + 向量检索 的本地知识管理系统",
)

add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

include_router(api_router)

@get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "PKM Knowledge Management System API", "version": "v2.0.0"}