import base64

from tmis.platform.rate_limiting.limiter import InMemoryRateLimiter
from tmis.platform.rate_limiting.schemas import RateLimitResult
from tmis.platform.security.encryption import EncryptionPort
from tmis.platform.security.secrets_rotation import RotatingEncryption, SecretRotationPort
from tmis.platform.security.tenant_isolation import TenantContext, require_same_firm


class IntegrationSecurityEngine:
    """Composes `tmis.platform.security` (encryption, secret rotation,
    tenant isolation) and `tmis.platform.rate_limiting` directly —
    "toutes les communications avec des systèmes externes doivent être
    chiffrées ... respecter les politiques de gouvernance de TMIS ...
    être isolées par tenant" plus "rotation des secrets et
    mécanismes de limitation de débit" (sprint requirements). TMIS
    already built all four pieces once at the platform layer (Sprint
    10) — the LIH never reimplements encryption, secret storage,
    rate limiting or tenant checks."""

    def __init__(
        self, encryption: EncryptionPort, rate_limiter: InMemoryRateLimiter
    ) -> None:
        self._encryption = encryption
        self._rate_limiter = rate_limiter

    def encrypt_config(self, config: dict[str, str]) -> dict[str, str]:
        return {
            key: base64.b64encode(self._encryption.encrypt(value.encode())).decode()
            for key, value in config.items()
        }

    def decrypt_config(self, encrypted_config: dict[str, str]) -> dict[str, str]:
        return {
            key: self._encryption.decrypt(base64.b64decode(value)).decode()
            for key, value in encrypted_config.items()
        }

    def check_rate_limit(self, connector_id: str) -> RateLimitResult:
        return self._rate_limiter.check(connector_id)

    def require_tenant(self, context: TenantContext, resource_firm_id: str) -> None:
        require_same_firm(context, resource_firm_id)


def new_rotating_encryption(rotation_store: SecretRotationPort) -> RotatingEncryption:
    return RotatingEncryption(rotation_store)
