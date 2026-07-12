from tmis.identity_platform.passwordless.schemas import PasswordlessChallenge


class InMemoryPasswordlessChallengeStore:
    def __init__(self) -> None:
        self._challenges: dict[tuple[str, str], PasswordlessChallenge] = {}

    def save(self, challenge: PasswordlessChallenge) -> None:
        self._challenges[(challenge.firm_id, challenge.id)] = challenge

    def get(self, firm_id: str, challenge_id: str) -> PasswordlessChallenge | None:
        return self._challenges.get((firm_id, challenge_id))
