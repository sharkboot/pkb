import httpx
from typing import Optional, Dict, Any
from core.config import settings

async def chat_completion(messages: list, **kwargs) -> str:
    """调用 LLM 聊天接口"""
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": settings.llm_model_name,
        "messages": messages,
        **kwargs
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.llm_base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

async def create_embedding(text: str) -> list:
    """调用 Embedding 接口生成向量"""
    headers = {
        "Authorization": f"Bearer {settings.final_embed_api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": settings.final_embed_model_name,
        "input": text,
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.final_embed_base_url}/embeddings",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]