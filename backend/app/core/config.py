from pathlib import Path
from typing import Any, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    PROJECT_NAME: str = "NexusRAG — Agentic Knowledge Intelligence Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            v_clean = v.strip().lower()
            if v_clean in ("true", "1", "yes", "t", "on", "dev", "development"):
                return True
            if v_clean in ("false", "0", "no", "f", "off", "release", "prod", "production"):
                return False
        return False
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "nexusrag-production-key-change-in-production-env"
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nexus:nexuspassword@localhost:5432/nexusrag_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM Provider Configuration
    LLM_PROVIDER: str = "openai"  # "openai", "groq", "ollama", "mock"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2048

    # Embeddings
    EMBEDDING_PROVIDER: str = "sentence_transformers"  # "sentence_transformers", "openai", "mock"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Reranker
    RERANKER_TYPE: str = "cross_encoder"  # "cross_encoder", "heuristic"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_TOP_K: int = 5

    # Retrieval parameters
    RETRIEVAL_TOP_K: int = 10
    RETRIEVAL_DENSE_WEIGHT: float = 0.6
    RETRIEVAL_SPARSE_WEIGHT: float = 0.4
    RRF_K: int = 60
    SIMILARITY_THRESHOLD: float = 0.35

    # Document Processing & Chunker
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    MAX_UPLOAD_SIZE_MB: int = 25
    UPLOAD_DIR: Path = Path("backend/uploads")

    # Guardrails & Observability
    ENABLE_GROUNDING_CHECK: bool = True
    GROUNDING_THRESHOLD: float = 0.70
    LOG_LEVEL: str = "INFO"

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL.lower()

    @property
    def is_postgres(self) -> bool:
        return "postgresql" in self.DATABASE_URL.lower() or "postgres" in self.DATABASE_URL.lower()


settings = Settings()
