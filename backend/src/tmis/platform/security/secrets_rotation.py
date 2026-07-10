from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from cryptography.fernet import Fernet, MultiFernet

from tmis.platform.security.encryption import generate_key


@dataclass(frozen=True, slots=True)
class SecretVersion:
    """One generation of a rotating secret — old versions stay around
    so ciphertexts encrypted before a rotation can still be decrypted
    (see docs/47-guide-securite-entreprise.md — Rotation des
    secrets)."""

    version: int
    value: bytes
    created_at: datetime


class SecretRotationPort(Protocol):
    """Port implemented by every interchangeable secret-rotation store.
    A real deployment would back this with a KMS/secrets manager
    (Vault, AWS Secrets Manager...) instead of the in-memory reference
    implementation shipped this sprint."""

    def current(self) -> SecretVersion: ...

    def rotate(self) -> SecretVersion: ...

    def list_versions(self) -> list[SecretVersion]: ...


class InMemorySecretRotationStore:
    """Implements `SecretRotationPort`: keeps every generated key in
    memory, newest first. Not persisted across restarts — a real
    deployment plugs in a KMS-backed store behind the same port."""

    def __init__(self) -> None:
        first = SecretVersion(version=1, value=generate_key(), created_at=datetime.now(UTC))
        self._versions: list[SecretVersion] = [first]

    def current(self) -> SecretVersion:
        return self._versions[-1]

    def rotate(self) -> SecretVersion:
        new_version = SecretVersion(
            version=self._versions[-1].version + 1,
            value=generate_key(),
            created_at=datetime.now(UTC),
        )
        self._versions.append(new_version)
        return new_version

    def list_versions(self) -> list[SecretVersion]:
        return list(self._versions)


class RotatingEncryption:
    """Implements `EncryptionPort` on top of a `SecretRotationPort`:
    encrypts with the newest key, decrypts with whichever version
    produced the ciphertext (via `cryptography.fernet.MultiFernet`) —
    so rotating the secret never breaks data encrypted before the
    rotation."""

    def __init__(self, rotation_store: SecretRotationPort) -> None:
        self._rotation_store = rotation_store

    def _multi_fernet(self) -> MultiFernet:
        versions = sorted(
            self._rotation_store.list_versions(), key=lambda v: v.version, reverse=True
        )
        return MultiFernet([Fernet(v.value) for v in versions])

    def encrypt(self, plaintext: bytes) -> bytes:
        return self._multi_fernet().encrypt(plaintext)

    def decrypt(self, ciphertext: bytes) -> bytes:
        return self._multi_fernet().decrypt(ciphertext)
