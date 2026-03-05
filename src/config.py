import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Adaptive Learning Core"
    VERSION: str = "0.1.0"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/adaptive_core"
    
    # LLM
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    
    # Voice
    WHISPER_MODEL: str = "tiny" # using tiny for speed in dev
    PIPER_VOICE: str = "en_US-amy-medium"
    
    # Cost/Runtime
    USE_LLM_FOR_SUMMARY: bool = False
    MAX_CONTEXT_CHARS: int = 12000
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
