from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    knowledge_base_path: str = "./knowledge_base"
    markdown_path: str = "./knowledge_base"
    
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model_name: str = "gpt-4"

    vision_api_key: str = ""
    vision_base_url: str = "https://api.openai.com/v1"
    vision_model_name: str = "gpt-4o"
    
    # Embedding configuration (reuse LLM config by default)
    embed_api_key: str = ""
    embed_base_url: str = ""
    embed_model_name: str = ""
    
    vector_store_enabled: bool = False
    vector_store_type: str = "chroma"  # chroma (local) | milvus
    vector_store_host: str = "localhost"
    vector_store_port: int = 19530
    vector_store_db: str = "default"
    # Chroma local persistent storage path
    vector_store_path: str = "./knowledge_base/vector_store"
    # Similarity threshold for semantic search (cosine distance; Chroma returns distance not similarity)
    semantic_search_min_similarity: float = 0.3
    
    auto_merge: bool = True
    auto_summary: bool = True
    
    # Scheduler settings for memory integration
    scheduler_enabled: bool = True
    daily_summary_enabled: bool = False
    weekly_summary_enabled: bool = False
    monthly_summary_enabled: bool = False
    daily_summary_time: str = "09:00"
    weekly_summary_day: int = 0  # 0=Monday
    weekly_summary_time: str = "09:00"
    monthly_summary_day: int = 1
    monthly_summary_time: str = "09:00"

    class Config:
        env_file = ".env"

    @property
    def final_embed_api_key(self) -> str:
        return self.embed_api_key or self.llm_api_key
    
    @property
    def final_embed_base_url(self) -> str:
        return self.embed_base_url or self.llm_base_url
    
    @property
    def final_embed_model_name(self) -> str:
        return self.embed_model_name or self.llm_model_name

settings = Settings()
