from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Insurance Claim Document Management Backend"
    API_PREFIX: str = "/api/v1"
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "insurance_claim_documents"
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    OCR_ENGINE_URL: str = ""
    OCR_API_URL: str = ""
    OCR_API_KEY: str = ""
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024, ge=1)
    ALLOWED_MIME_TYPES: tuple[str, ...] = (
        "application/pdf",
        "image/png",
        "image/jpeg",
    )
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_CREDENTIALS: bool = False
    CORS_ALLOW_METHODS: list[str] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_HEADERS: list[str] = Field(default_factory=lambda: ["*"])
    LOG_LEVEL: str = "INFO"
    OCR_PROVIDER_NAME: str = "external-ocr"
    MAPPER_VERSION: str = "v1"
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    def model_post_init(self, __context: Any) -> None:  # noqa: D401
        """Normalize configurable values after loading."""
        self.ALLOWED_MIME_TYPES = tuple(self.ALLOWED_MIME_TYPES)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
