from typing import Dict, Any
from models.schemas import SystemConfig
from core.config import settings

class SystemService:
    def __init__(self):
        self.config = {
            "markdown_path": settings.markdown_path,
            "llm_api_key": settings.llm_api_key,
            "llm_base_url": settings.llm_base_url,
            "llm_model_name": settings.llm_model_name,
            "embed_api_key": settings.embed_api_key,
            "embed_base_url": settings.embed_base_url,
            "embed_model_name": settings.embed_model_name,
            "vector_store_enabled": settings.vector_store_enabled,
            "vector_store_type": settings.vector_store_type,
            "vector_store_host": settings.vector_store_host,
            "vector_store_port": settings.vector_store_port,
            "vector_store_db": settings.vector_store_db,
            "auto_merge": settings.auto_merge,
            "auto_summary": settings.auto_summary,
        }

    def get_config(self) -> SystemConfig:
        return SystemConfig(**self.config)

    def update_config(self, config: SystemConfig) -> SystemConfig:
        self.config["markdown_path"] = config.markdown_path
        self.config["llm_api_key"] = config.llm_api_key
        self.config["llm_base_url"] = config.llm_base_url
        self.config["llm_model_name"] = config.llm_model_name
        self.config["embed_api_key"] = config.embed_api_key
        self.config["embed_base_url"] = config.embed_base_url
        self.config["embed_model_name"] = config.embed_model_name
        self.config["vector_store_enabled"] = config.vector_store_enabled
        self.config["vector_store_type"] = config.vector_store_type
        self.config["vector_store_host"] = config.vector_store_host
        self.config["vector_store_port"] = config.vector_store_port
        self.config["vector_store_db"] = config.vector_store_db
        self.config["auto_merge"] = config.auto_merge
        self.config["auto_summary"] = config.auto_summary
        
        return SystemConfig(**self.config)