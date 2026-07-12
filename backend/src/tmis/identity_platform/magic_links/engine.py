from jose import JWTError

from tmis.core.security import create_access_token, decode_access_token
from tmis.identity_platform.magic_links.ports import UsedMagicLinkStorePort

_PURPOSE_CLAIM = "purpose"
_MAGIC_LINK_PURPOSE = "magic_link"


class MagicLinkEngine:
    """A single-use, signed login link. Reuses
    `tmis.core.security.create_access_token`/`decode_access_token`
    directly for signing and verification rather than reimplementing
    JWT handling — the short-lived token's `exp` claim (from
    `tmis.core.config.access_token_expire_minutes`) bounds its
    lifetime, and the used-token store makes it single-use even though
    JWTs are normally stateless and replayable until expiry."""

    def __init__(self, used_store: UsedMagicLinkStorePort) -> None:
        self._used = used_store

    def issue(self, firm_id: str, user_id: str) -> str:
        return create_access_token(
            user_id, {"firm_id": firm_id, _PURPOSE_CLAIM: _MAGIC_LINK_PURPOSE}
        )

    def consume(self, token: str) -> str | None:
        if self._used.is_used(token):
            return None
        try:
            claims = decode_access_token(token)
        except JWTError:
            return None
        if claims.get(_PURPOSE_CLAIM) != _MAGIC_LINK_PURPOSE:
            return None
        self._used.mark_used(token)
        return str(claims["sub"])
