from typing import List, Dict, AsyncGenerator
from src.llm.providers.base import LLMProvider

class MockProvider(LLMProvider):
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        return "I am in fallback mode (Mock LLM). Please check your primary LLM connection."

    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        yield "Fallback mode active. "
        yield "Primary LLM unavailable."

    async def check_health(self) -> bool:
        return True
