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
    license_signing_key: str = "change-me-in-production"
    plugin_signing_key: str = "change-me-in-production"
    backup_storage_dir: str = "var/backups"

    default_model_provider: str = "openai"

    # --- Sprint 27: real RAG/connector adapters, behind the Sprint 2/5 ports ---
    # Vector index: "memory" keeps `InMemoryVectorIndex` (dev/tests default,
    # zero external dependency); "qdrant" switches to `QdrantVectorIndex`.
    rag_vector_index_backend: str = "memory"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "tmis_rag_chunks"
    qdrant_timeout_seconds: float = 10.0

    # Embeddings: "hashing" keeps `HashingEmbeddingProvider` (dev/tests
    # default, zero external dependency, no download); "sentence_transformers"
    # switches to a local embedding model (still no API key required).
    embedding_backend: str = "hashing"
    sentence_transformer_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # Connectors — codes/jurisprudence via the PISTE gateway (DILA), which
    # fronts both Légifrance and Judilibre behind the same OAuth2
    # client-credentials flow. Left unset, the codes/jurisprudence/doctrine
    # connectors keep using their Sprint 2 in-memory fixtures.
    piste_client_id: str | None = None
    piste_client_secret: str | None = None
    piste_oauth_token_url: str = "https://oauth.piste.gouv.fr/api/oauth/token"
    legifrance_api_base_url: str = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
    judilibre_api_base_url: str = "https://api.piste.gouv.fr/cassation/judilibre"

    # Connectors — generic configurable HTTP source, used for doctrine (no
    # applicable free public API) and for the Legal Research Engine's own
    # connectors (internal documentation, licensed private database), which
    # are firm-specific by nature. Each is independently optional; an unset
    # base URL keeps that connector on its Sprint 2/5 in-memory fixture.
    doctrine_connector_base_url: str | None = None
    doctrine_connector_api_key: str | None = None
    internal_documentation_connector_base_url: str | None = None
    internal_documentation_connector_api_key: str | None = None
    private_database_connector_base_url: str | None = None
    private_database_connector_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
