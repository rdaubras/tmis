import hashlib
import secrets

_KEY_PREFIX_LENGTH = 8


def generate_secret() -> str:
    """Generates an opaque, URL-safe secret — used for both API keys
    and OAuth client secrets (see docs/44-guide-api-publique.md)."""
    return secrets.token_urlsafe(32)


def hash_secret(raw_secret: str) -> str:
    """Hashes a secret with SHA-256 for storage — secrets are opaque
    high-entropy tokens (not user-chosen passwords), so a fast hash is
    appropriate here, unlike `tmis.core.security`'s password hashing."""
    return hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()


def key_prefix(raw_secret: str) -> str:
    """The visible, non-secret portion shown back to the user so they
    can recognise a key in a list without ever seeing it again."""
    return raw_secret[:_KEY_PREFIX_LENGTH]
