import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "EduVision Adaptive Learning Core"
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION_TO_A_STRONG_SECRET"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "https://eduvision.github.io"
    ]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/adaptive_core"
    
    # LLM (Together AI)
    TOGETHER_API_KEY: str = ""
    TOGETHER_MODEL: str = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Voice / Audio
    WHISPER_MODEL: str = "tiny" # using tiny for speed in dev
    PIPER_VOICE: str = "en_US-amy-medium"
    
    # Cost/Runtime & Limits
    USE_LLM_FOR_SUMMARY: bool = False
    MAX_CONTEXT_CHARS: int = 12000
    VECTOR_SEARCH_LIMIT: int = 5
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # Pydantic Settings Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        _env_file_encoding="utf-8"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
