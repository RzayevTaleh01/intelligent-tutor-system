import httpx
from typing import List, Dict, Any
from src.config import get_settings

settings = get_settings()

class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL

    async def generate_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Sends chat messages to Ollama and returns the response content.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
        except Exception as e:
            print(f"Ollama Error: {e}")
            return "I apologize, but I am having trouble connecting to my thought process (Ollama) right now."
