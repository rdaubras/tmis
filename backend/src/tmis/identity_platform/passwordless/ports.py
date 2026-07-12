from typing import Protocol

from tmis.identity_platform.passwordless.schemas import PasswordlessChallenge


class PasswordlessChallengeStorePort(Protocol):
    def save(self, challenge: PasswordlessChallenge) -> None: ...

    def get(self, firm_id: str, challenge_id: str) -> PasswordlessChallenge | None: ...
