from typing import Protocol

from cryptography.fernet import Fernet, InvalidToken


class EncryptionPort(Protocol):
    """Port implemented by every interchangeable at-rest encryption
    backend (see docs/47-guide-securite-entreprise.md — Chiffrement).
    The same port secures sensitive field data, uploaded documents, and
    backup archives — three *use sites*, one mechanism, so a future
    KMS-backed implementation only needs to be written once."""

    def encrypt(self, plaintext: bytes) -> bytes: ...

    def decrypt(self, ciphertext: bytes) -> bytes: ...


def generate_key() -> bytes:
    """Generates a new symmetric key — store it in a secrets manager
    (see `security/secrets_rotation.py`), never in source control."""
    return Fernet.generate_key()


class FernetEncryption:
    """Implements `EncryptionPort` with Fernet (AES-128-CBC + HMAC,
    from the `cryptography` package already in TMIS's dependency tree
    via `python-jose[cryptography]`). Authenticated encryption: a
    tampered or corrupted ciphertext raises `ValueError` rather than
    silently returning garbage."""

    def __init__(self, key: bytes) -> None:
        self._fernet = Fernet(key)

    def encrypt(self, plaintext: bytes) -> bytes:
        return self._fernet.encrypt(plaintext)

    def decrypt(self, ciphertext: bytes) -> bytes:
        try:
            return self._fernet.decrypt(ciphertext)
        except InvalidToken as exc:
            raise ValueError("Ciphertext is invalid, tampered with, or uses a wrong key") from exc
