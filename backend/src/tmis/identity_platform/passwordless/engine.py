from datetime import UTC, datetime

from tmis.identity_platform.passwordless.ports import PasswordlessChallengeStorePort
from tmis.identity_platform.passwordless.schemas import (
    PasswordlessChallenge,
    generate_code,
    new_challenge_expiry,
    new_challenge_id,
)


class PasswordlessEngine:
    """One-time-code passwordless login — the code is generated here
    and handed to the caller to deliver out-of-band (email/SMS); this
    engine never sends it itself, staying delivery-channel agnostic."""

    def __init__(self, store: PasswordlessChallengeStorePort) -> None:
        self._store = store

    def request(self, firm_id: str, user_id: str) -> PasswordlessChallenge:
        challenge = PasswordlessChallenge(
            id=new_challenge_id(),
            firm_id=firm_id,
            user_id=user_id,
            code=generate_code(),
            expires_at=new_challenge_expiry(),
        )
        self._store.save(challenge)
        return challenge

    def verify(self, firm_id: str, challenge_id: str, code: str) -> str | None:
        challenge = self._store.get(firm_id, challenge_id)
        if (
            challenge is None
            or challenge.used
            or challenge.code != code
            or challenge.expires_at < datetime.now(UTC)
        ):
            return None
        challenge.used = True
        self._store.save(challenge)
        return challenge.user_id
