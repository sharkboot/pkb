import asyncio
import sys
sys.path.insert(0, '.')

from src.core.config import settings
from src.llm.provider import chat_completion

print("=== PKM LLM Configuration Check ===")
print(f"LLM Model: {settings.llm_model_name}")
print(f"LLM API Base: {settings.llm_base_url}")
api_key_display = settings.llm_api_key[:10] + "..." if settings.llm_api_key else "Not configured"
print(f"LLM API Key: {api_key_display}")
print(f"Embedding Model: {settings.final_embed_model_name}")
print(f"Embedding API Base: {settings.final_embed_base_url}")
print("==============================\n")

async def test_llm():
    if not settings.llm_api_key:
        print("ERROR: LLM API Key not configured, please set LLM_API_KEY in .env file")
        return
    
    try:
        print("OK: LLM API configured successfully")
        
        print("\nSending test request...")
        response = await chat_completion(
            messages=[{"role": "user", "content": "请简单回复'测试成功'"}]
        )
        
        print(f"OK: LLM Response: {response}")
        
    except Exception as e:
        print(f"ERROR: Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_llm())