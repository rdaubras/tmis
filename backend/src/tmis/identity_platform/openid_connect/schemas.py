from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OidcTokenResponse:
    access_token: str
    refresh_token: str
    id_token: str
    token_type: str = "Bearer"
