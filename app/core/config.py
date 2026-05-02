from __future__ import annotations

from functools import lru_cache
from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JobPilot Agent"
    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./jobpilot.db"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "jobpilot_documents"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8501"])

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

