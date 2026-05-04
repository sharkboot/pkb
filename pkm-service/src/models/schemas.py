from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from models.enums import SourceType, KnowledgeStatus, TaskType

class BaseResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None

class PaginationResponse(BaseModel):
    list: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20

class PaginationResponseWrapper(BaseResponse):
    data: PaginationResponse = PaginationResponse()

class ContentCollectRequest(BaseModel):
    source_type: SourceType = Field(..., alias="sourceType")
    content: Optional[str] = None
    images: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = {
        "populate_by_name": True
    }

class KnowledgeUnit(BaseModel):
    id: UUID
    title: str
    summary: Optional[str] = None
    content: str
    source_refs: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    relations: Optional[List[str]] = []
    status: KnowledgeStatus = KnowledgeStatus.DRAFT
    category: Optional[str] = None
    source: Optional[str] = None
    score: float = 0.0
    created_at: datetime
    updated_at: datetime

class KnowledgeCreateRequest(BaseModel):
    title: str
    summary: Optional[str] = None
    content: str
    source_refs: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    relations: Optional[List[str]] = []
    status: Optional[KnowledgeStatus] = KnowledgeStatus.DRAFT

class KnowledgeUpdateRequest(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    relations: Optional[List[str]] = None
    status: Optional[KnowledgeStatus] = None
    category: Optional[str] = None

class Session(BaseModel):
    id: UUID
    title: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class SessionCreateRequest(BaseModel):
    title: Optional[str] = None

class Task(BaseModel):
    id: UUID
    task_type: TaskType = Field(..., alias="taskType")
    target_id: Optional[str] = Field(None, alias="targetId")
    params: Optional[Dict[str, Any]] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "populate_by_name": True
    }

class TaskCreateRequest(BaseModel):
    task_type: TaskType = Field(..., alias="taskType")
    target_id: Optional[str] = Field(None, alias="targetId")
    params: Optional[Dict[str, Any]] = None

    model_config = {
        "populate_by_name": True
    }

class Category(BaseModel):
    id: UUID
    name: str
    parent_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

class CategoryCreateRequest(BaseModel):
    name: str
    parent_id: Optional[UUID] = None

class SystemConfig(BaseModel):
    markdown_path: str = Field(..., alias="markdownPath")
    
    llm_api_key: str = Field("", alias="llmApiKey")
    llm_base_url: str = Field("https://api.openai.com/v1", alias="llmBaseUrl")
    llm_model_name: str = Field("gpt-4", alias="llmModelName")
    
    embed_api_key: str = Field("", alias="embedApiKey")
    embed_base_url: str = Field("https://api.openai.com/v1", alias="embedBaseUrl")
    embed_model_name: str = Field("text-embedding-ada-002", alias="embedModelName")
    
    vector_store_enabled: bool = Field(False, alias="vectorStoreEnabled")
    vector_store_type: str = Field("milvus", alias="vectorStoreType")
    vector_store_host: str = Field("localhost", alias="vectorStoreHost")
    vector_store_port: int = Field(19530, alias="vectorStorePort")
    vector_store_db: str = Field("default", alias="vectorStoreDb")
    
    auto_merge: bool = Field(True, alias="autoMerge")
    auto_summary: bool = Field(True, alias="autoSummary")

class FileUploadResponse(BaseModel):
    url: str
    filename: str
    folder: Optional[str] = None