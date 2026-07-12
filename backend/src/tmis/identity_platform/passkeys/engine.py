from tmis.identity_platform.webauthn.engine import WebAuthnEngine
from tmis.identity_platform.webauthn.ports import WebAuthnCredentialStorePort


class PasskeyEngine:
    """Passkeys are WebAuthn credentials used *usernameless*: the
    caller doesn't know which user it's authenticating until the
    credential itself resolves to one. Composes `webauthn.
    WebAuthnEngine` directly for the ceremony; adds only
    credential-id-based user resolution — never reimplements
    signature-counter replay protection."""

    def __init__(self, webauthn_engine: WebAuthnEngine, store: WebAuthnCredentialStorePort) -> None:
        self._webauthn = webauthn_engine
        self._store = store

    def authenticate(self, firm_id: str, credential_id: str, signature_counter: int) -> str | None:
        if not self._webauthn.verify_assertion(firm_id, credential_id, signature_counter):
            return None
        credential = self._store.get(firm_id, credential_id)
        return credential.user_id if credential is not None else None
