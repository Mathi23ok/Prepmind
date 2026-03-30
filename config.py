from functools import lru_cache
from os import getenv
from typing import Final

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = "GATEPrep AI"
    app_description: str = (
        "Study assistant for uploading PDFs, asking grounded questions, "
        "and generating revision flashcards."
    )
    jwt_secret_key: str = Field(
        default_factory=lambda: getenv("JWT_SECRET_KEY", "dev-only-change-me"),
    )
    jwt_algorithm: str = Field(default_factory=lambda: getenv("JWT_ALGORITHM", "HS256"))
    access_token_expiry_hours: int = Field(
        default_factory=lambda: int(getenv("ACCESS_TOKEN_EXPIRY_HOURS", "12")),
        ge=1,
        le=168,
    )
    max_upload_size_mb: int = Field(
        default_factory=lambda: int(getenv("MAX_UPLOAD_SIZE_MB", "20")),
        ge=1,
        le=100,
    )
    chunk_size_words: int = Field(
        default_factory=lambda: int(getenv("CHUNK_SIZE_WORDS", "120")),
        ge=50,
        le=500,
    )
    top_k_chunks: int = Field(
        default_factory=lambda: int(getenv("TOP_K_CHUNKS", "5")),
        ge=1,
        le=10,
    )
    similarity_threshold: float = Field(
        default_factory=lambda: float(getenv("SIMILARITY_THRESHOLD", "1.5")),
        ge=0.1,
        le=5.0,
    )
    frontend_mount_path: Final[str] = "/frontend"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
