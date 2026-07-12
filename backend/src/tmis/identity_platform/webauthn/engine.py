from tmis.identity_platform.webauthn.ports import WebAuthnCredentialStorePort
from tmis.identity_platform.webauthn.schemas import WebAuthnCredential


class WebAuthnEngine:
    """Reference WebAuthn/passkey ceremony — logical only: this
    in-memory implementation checks an opaque public-key string and
    enforces the monotonically increasing signature counter WebAuthn
    assertions carry (the standard replay-protection signal), but does
    not parse a real COSE public key or verify a real
    attestation/assertion cryptographic signature. A production
    deployment replaces this engine with one backed by a library such
    as `webauthn`/`fido2`, behind the same
    `WebAuthnCredentialStorePort` — same architecture-only extension
    point pattern already used by `platform.security.sso.
    OidcProviderPort` (Sprint 10)."""

    def __init__(self, store: WebAuthnCredentialStorePort) -> None:
        self._store = store

    def register_credential(
        self, firm_id: str, user_id: str, credential_id: str, public_key: str
    ) -> WebAuthnCredential:
        credential = WebAuthnCredential(
            id=credential_id, firm_id=firm_id, user_id=user_id, public_key=public_key
        )
        self._store.save(credential)
        return credential

    def verify_assertion(self, firm_id: str, credential_id: str, signature_counter: int) -> bool:
        credential = self._store.get(firm_id, credential_id)
        if credential is None or signature_counter <= credential.sign_count:
            return False
        credential.sign_count = signature_counter
        self._store.save(credential)
        return True
