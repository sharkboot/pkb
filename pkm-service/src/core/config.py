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
    
    # Embedding 配置默认复用 LLM 配置
    embed_api_key: str = ""
    embed_base_url: str = ""
    embed_model_name: str = ""
    
    vector_store_enabled: bool = False
    vector_store_type: str = "milvus"
    vector_store_host: str = "localhost"
    vector_store_port: int = 19530
    vector_store_db: str = "default"
    
    auto_merge: bool = True
    auto_summary: bool = True

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