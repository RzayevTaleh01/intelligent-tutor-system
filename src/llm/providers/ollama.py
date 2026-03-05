import httpx
import json
from typing import List, Dict, AsyncGenerator
from src.llm.providers.base import LLMProvider
from src.config import get_settings

settings = get_settings()

class OllamaProvider(LLMProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL

    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        url = f"{self.base_url}/api/chat"
        # Optimize for speed: reduce context window or max tokens if possible
        # Add options to limit generation time
        options = kwargs.get("options", {})
        if "num_predict" not in options:
            options["num_predict"] = 150 # Limit output tokens for speed
        
        payload = {
            "model": self.model, 
            "messages": messages, 
            "stream": False, 
            "options": options,
            **kwargs
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json().get("message", {}).get("content", "")
        except Exception as e:
            print(f"Ollama Generate Error: {e}")
            # Fallback for now if not handled upstream, or re-raise if upstream handles it
            # But since v2_main relies on active_llm which might be ollama even if it fails transiently
            raise e

    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/api/chat"
        payload = {"model": self.model, "messages": messages, "stream": True, **kwargs}
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            chunk = data.get("message", {}).get("content", "")
                            if chunk: yield chunk
                        except: continue

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except:
            return False
