import base64
from datetime import UTC, datetime

from tmis.identity_platform.secret_manager.ports import ManagedSecretStorePort
from tmis.identity_platform.secret_manager.schemas import ManagedSecret
from tmis.platform.security.encryption import EncryptionPort
from tmis.platform.security.secrets_rotation import RotatingEncryption, SecretRotationPort


def new_rotating_encryption(rotation_store: SecretRotationPort) -> RotatingEncryption:
    return RotatingEncryption(rotation_store)


class SecretManagerEngine:
    """The firm-wide, canonical secret store — "les clés API et
    secrets d'intégration ne doivent jamais être stockés en clair"
    (sprint requirement: chiffrement, rotation, contrôle d'accès,
    journalisation). Composes `platform.security.encryption`/
    `secrets_rotation` directly (Sprint 10) — the same reuse pattern
    `integration_hub.security` already established (Sprint 18) — and
    never reimplements either. Access control is layered on top by
    the caller via `authorization.AuthorizationEngine` (Permission.
    SECRET_MANAGE); journalisation is layered on top via
    `security_events`."""

    def __init__(self, store: ManagedSecretStorePort, encryption: EncryptionPort) -> None:
        self._store = store
        self._encryption = encryption

    def set_secret(self, firm_id: str, key: str, plaintext: str) -> ManagedSecret:
        existing = self._store.get(firm_id, key)
        encrypted_value = base64.b64encode(self._encryption.encrypt(plaintext.encode())).decode()
        secret = ManagedSecret(
            key=key,
            firm_id=firm_id,
            encrypted_value=encrypted_value,
            created_at=existing.created_at if existing is not None else datetime.now(UTC),
            rotated_at=datetime.now(UTC) if existing is not None else None,
        )
        self._store.save(secret)
        return secret

    def get_secret(self, firm_id: str, key: str) -> str | None:
        record = self._store.get(firm_id, key)
        if record is None:
            return None
        return self._encryption.decrypt(base64.b64decode(record.encrypted_value)).decode()

    def list_keys(self, firm_id: str) -> list[str]:
        return [s.key for s in self._store.list_for_firm(firm_id)]

    def list_for_firm(self, firm_id: str) -> list[ManagedSecret]:
        """Metadata only — `ManagedSecret.encrypted_value` is
        ciphertext, never the plaintext, so this is safe to expose
        directly (e.g. via the API) without decrypting."""
        return self._store.list_for_firm(firm_id)
