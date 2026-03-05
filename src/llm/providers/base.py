from abc import ABC, abstractmethod
from typing import List, Dict, AsyncGenerator

class LLMProvider(ABC):
    @abstractmethod
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        pass

    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        pass
