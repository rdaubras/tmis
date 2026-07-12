from tmis.identity_platform.mfa.schemas import TotpEnrollment


class InMemoryTotpEnrollmentStore:
    def __init__(self) -> None:
        self._enrollments: dict[tuple[str, str], TotpEnrollment] = {}

    def save(self, enrollment: TotpEnrollment) -> None:
        self._enrollments[(enrollment.firm_id, enrollment.user_id)] = enrollment

    def get(self, firm_id: str, user_id: str) -> TotpEnrollment | None:
        return self._enrollments.get((firm_id, user_id))

    def list_for_firm(self, firm_id: str) -> list[TotpEnrollment]:
        return [e for (fid, _), e in self._enrollments.items() if fid == firm_id]
