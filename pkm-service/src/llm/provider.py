from openai import OpenAI
from typing import Optional, Dict, Any, List
import asyncio
import base64
import httpx
from core.config import settings


def _create_httpx_client() -> httpx.Client:
    """创建 httpx 客户端，禁用代理自动检测避免版本兼容问题"""
    return httpx.Client(timeout=60.0)


def _get_openai_client() -> OpenAI:
    """创建文本 LLM 客户端"""
    return OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        http_client=_create_httpx_client(),
    )


def _get_vision_client() -> OpenAI:
    """创建视觉模型客户端"""
    return OpenAI(
        api_key=settings.vision_api_key or settings.llm_api_key,
        base_url=settings.vision_base_url or settings.llm_base_url,
        http_client=_create_httpx_client(),
    )


def _get_embed_client() -> OpenAI:
    """创建 Embedding 专用客户端"""
    return OpenAI(
        api_key=settings.final_embed_api_key,
        base_url=settings.final_embed_base_url,
        http_client=_create_httpx_client(),
    )


async def chat_completion(messages: list, **kwargs) -> str:
    """调用 LLM 聊天接口"""
    client = _get_openai_client()

    def _call():
        response = client.chat.completions.create(
            model=settings.llm_model_name,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content

    return await asyncio.to_thread(_call)


async def chat_completion_with_images(
    messages: List[Dict[str, Any]],
    image_urls: Optional[List[str]] = None,
    **kwargs
) -> str:
    """调用支持图片的 LLM 聊天接口（多模态）"""
    # 下载图片
    image_contents = []
    if image_urls:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            for url in image_urls:
                try:
                    if url.startswith("data:image"):
                        image_contents.append(url)
                    else:
                        resp = await http_client.get(url)
                        resp.raise_for_status()
                        content_type = resp.headers.get("content-type", "image/jpeg")
                        b64_data = base64.b64encode(resp.content).decode("utf-8")
                        image_contents.append(f"data:{content_type};base64,{b64_data}")
                except Exception:
                    continue

    client = _get_vision_client()

    def _call():
        final_messages = []
        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "user")

            if image_contents:
                parts = [{"type": "text", "text": content}] if content else []
                for img in image_contents:
                    parts.append({
                        "type": "image_url",
                        "image_url": {"url": img}
                    })
                final_messages.append({"role": role, "content": parts})
            else:
                final_messages.append({"role": role, "content": content})

        response = client.chat.completions.create(
            model=settings.vision_model_name,
            messages=final_messages,
            **kwargs
        )
        return response.choices[0].message.content

    return await asyncio.to_thread(_call)


async def create_embedding(text: str) -> list:
    """调用 Embedding 接口生成向量"""
    client = _get_embed_client()

    def _call():
        response = client.embeddings.create(
            model=settings.final_embed_model_name,
            input=text,
        )
        return response.data[0].embedding

    return await asyncio.to_thread(_call)


async def create_embedding_cached(text: str) -> list:
    """调用 Embedding 接口生成向量（带本地缓存，内容未变化时直接返回缓存）"""
    from storage.embedding_cache import embedding_cache

    cached = embedding_cache.get(text)
    if cached is not None:
        return cached

    embedding = await create_embedding(text)
    embedding_cache.set(text, embedding)
    return embedding


async def create_embeddings(texts: List[str]) -> List[List[float]]:
    """批量调用 Embedding 接口（单次请求，多条输入）

    OpenAI 兼容 API 支持一次传入多条文本，减少网络往返。
    单条时走缓存路径。
    """
    from storage.embedding_cache import embedding_cache
    from typing import List

    # 先查缓存
    results: List[Optional[List[float]]] = [None] * len(texts)
    cache_hits: Dict[int, List[float]] = {}
    to_fetch: List[int] = []

    for i, text in enumerate(texts):
        cached = embedding_cache.get(text)
        if cached is not None:
            cache_hits[i] = cached
        else:
            to_fetch.append(i)

    for i in cache_hits:
        results[i] = cache_hits[i]

    # 批量获取未命中的
    if to_fetch:
        client = _get_embed_client()

        def _batch_call():
            response = client.embeddings.create(
                model=settings.final_embed_model_name,
                input=[texts[i] for i in to_fetch],
            )
            return response.data

        data = await asyncio.to_thread(_batch_call)
        for j, idx in enumerate(to_fetch):
            emb = data[j].embedding
            results[idx] = emb
            embedding_cache.set(texts[idx], emb)

    return results
