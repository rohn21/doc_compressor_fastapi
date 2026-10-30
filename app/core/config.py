"""Application configuration and settings using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration parameters for document compressor."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = False
    APP_NAME: str = "Document Compressor"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Database parameters
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "document_compressor"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Explicit URI overrides
    DATABASE_URL: str | None = None
    ASYNC_DATABASE_URL: str | None = None

    # Redis and Queue
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage parameters
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_DIR: str = "./storage"
    MAX_FILE_SIZE_MB: int = 50
    MAX_BATCH_FILES: int = 20

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_uri(self) -> str:
        """Synchronous database connection URI (used by Alembic and sync tools)."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_uri(self) -> str:
        """Asynchronous database connection URI (used by FastAPI runtime)."""
        if self.ASYNC_DATABASE_URL:
            return self.ASYNC_DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
