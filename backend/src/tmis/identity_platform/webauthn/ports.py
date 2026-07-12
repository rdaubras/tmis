from typing import Protocol

from tmis.identity_platform.webauthn.schemas import WebAuthnCredential


class WebAuthnCredentialStorePort(Protocol):
    def save(self, credential: WebAuthnCredential) -> None: ...

    def get(self, firm_id: str, credential_id: str) -> WebAuthnCredential | None: ...
