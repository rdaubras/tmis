from dataclasses import dataclass


@dataclass(slots=True)
class WebAuthnCredential:
    id: str
    firm_id: str
    user_id: str
    public_key: str
    sign_count: int = 0
