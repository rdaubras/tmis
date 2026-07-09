from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class KernelConfig(BaseSettings):
    """AI Kernel settings, loaded from environment variables (12-factor)."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="TMIS_AI_", extra="ignore")

    default_provider: str = "openai"
    default_connectors: list[str] = ["codes", "jurisprudence", "doctrine"]
    cache_ttl_seconds: int = 300
    use_cache: bool = True


@lru_cache
def get_kernel_config() -> KernelConfig:
    return KernelConfig()
