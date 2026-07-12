from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Career Intelligence Platform API"
    app_version: str = "0.1.0"
    environment: str = Field(default="local")
    enable_docs: bool = True

    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_secret: str | None = None
    supabase_storage_bucket: str = "candidate-documents"

    ai_provider: str | None = None
    ai_model: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
