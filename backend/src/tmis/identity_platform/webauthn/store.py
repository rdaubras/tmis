from tmis.identity_platform.webauthn.schemas import WebAuthnCredential


class InMemoryWebAuthnCredentialStore:
    def __init__(self) -> None:
        self._credentials: dict[tuple[str, str], WebAuthnCredential] = {}

    def save(self, credential: WebAuthnCredential) -> None:
        self._credentials[(credential.firm_id, credential.id)] = credential

    def get(self, firm_id: str, credential_id: str) -> WebAuthnCredential | None:
        return self._credentials.get((firm_id, credential_id))
