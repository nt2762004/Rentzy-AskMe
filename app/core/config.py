from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Rentzy Knowledge Base API"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # PostgreSQL Config
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "rentzy_kb"
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/rentzy_kb"

    # Qdrant Config
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "rentzy_knowledge"
    QDRANT_URL: str = "http://localhost:6333"

    # Redis Config
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_TTL: int = 86400
    REDIS_URL: Optional[str] = None

    # Gemini & Embedding Config
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL_NAME: str = "gemini-flash-lite-latest"
    EMBEDDING_MODEL_NAME: str = "gemini-embedding-2"
    EMBEDDING_DIMENSION: int = 3072

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
