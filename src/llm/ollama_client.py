import httpx
import json
from typing import List, Dict, Any, AsyncGenerator
from src.config import get_settings

settings = get_settings()

class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL

    async def check_connection(self) -> bool:
        """
        Checks if Ollama is reachable and the model exists.
        """
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    models = [m["name"] for m in resp.json().get("models", [])]
                    print(f"Ollama Connected. Available models: {models}")
                    if self.model not in models and f"{self.model}:latest" not in models:
                         print(f"WARNING: Model '{self.model}' not found in Ollama. Please run 'ollama pull {self.model}'")
                    return True
        except Exception as e:
            print(f"Ollama Connection Failed: {e}")
            print("Tip: Ensure Ollama is running on the host and accessible (try OLLAMA_HOST=0.0.0.0)")
            return False
        return False

    async def generate_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Sends chat messages to Ollama and returns the full response content.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
        except Exception as e:
            print(f"Ollama Error: {e}")
            return "I apologize, but I am having trouble connecting to my AI brain (Ollama). However, I can still generate exercises and track your progress based on the lesson content. Please continue practicing!"

    async def stream_chat_completion(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Streams chat completion chunks.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                chunk = data.get("message", {}).get("content", "")
                                if chunk:
                                    yield chunk
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            print(f"Ollama Stream Error: {e}")
            yield f"[Error: {str(e)}]"
