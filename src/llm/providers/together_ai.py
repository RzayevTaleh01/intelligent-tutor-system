import httpx
import json
import logging
from typing import List, Dict, AsyncGenerator
from src.llm.providers.base import LLMProvider
from src.config import get_settings

settings = get_settings()
logger = logging.getLogger("eduvision.llm.together")

class TogetherProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.TOGETHER_API_KEY
        self.model = settings.TOGETHER_MODEL
        self.base_url = "https://api.together.xyz/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        url = f"{self.base_url}/chat/completions"
        
        # Merge default params with kwargs
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.7),
            "top_k": kwargs.get("top_k", 50),
            "repetition_penalty": kwargs.get("repetition_penalty", 1.0)
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            # Increased timeout to 120 seconds for production resilience
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                if "choices" in data:
                    return data["choices"][0]["message"]["content"]
                elif "error" in data:
                    logger.error(f"Together AI API Error: {data['error']}")
                    raise Exception(f"Together AI API Error: {data['error']}")
                else:
                    logger.error(f"Unexpected response format: {data}")
                    raise Exception(f"Unexpected response format: {data}")

        except httpx.HTTPStatusError as e:
            logger.error(f"Together AI HTTP Error: {e.response.text}")
            raise e
        except Exception as e:
            logger.error(f"Together AI Error: {str(e)}")
            raise e

    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.7),
            "top_k": kwargs.get("top_k", 50),
            "repetition_penalty": kwargs.get("repetition_penalty", 1.0)
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload, headers=self.headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                chunk = data["choices"][0]["delta"].get("content", "")
                                if chunk:
                                    yield chunk
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Together AI Stream Error: {str(e)}")
            yield f"[Error: {str(e)}]"

    async def check_health(self) -> bool:
        """
        Checks if the API key is valid by listing models.
        """
        url = f"{self.base_url}/models"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Together AI Health Check Failed: {str(e)}")
            return False
