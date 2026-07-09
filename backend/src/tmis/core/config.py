from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables (12-factor)."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="TMIS_", extra="ignore")

    app_name: str = "TMIS - Themis Intelligence System"
    environment: str = "development"
    debug: bool = False

    api_v1_prefix: str = "/api/v1"
    cors_allowed_origins: list[str] = ["http://localhost:3000"]

    database_url: str = "postgresql+psycopg://tmis:tmis@localhost:5432/tmis"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    default_model_provider: str = "openai"


@lru_cache
def get_settings() -> Settings:
    return Settings()
