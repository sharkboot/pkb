from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from api import api_router
from core.config import settings
from services.scheduler_service import scheduler_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting PKM server...")
    scheduler_service.start()
    logger.info("Scheduler started")
    yield
    # Shutdown
    scheduler_service.stop()
    logger.info("PKM server stopped")


app = FastAPI(
    title="PKM Knowledge Management System",
    version="v2.1.0",
    description="Local knowledge management system with LLM + Markdown + Vector search",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "PKM Knowledge Management System API", "version": "v2.1.0"}
