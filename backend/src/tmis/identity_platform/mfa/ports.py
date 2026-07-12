from typing import Protocol

from tmis.identity_platform.mfa.schemas import TotpEnrollment


class TotpEnrollmentStorePort(Protocol):
    def save(self, enrollment: TotpEnrollment) -> None: ...

    def get(self, firm_id: str, user_id: str) -> TotpEnrollment | None: ...

    def list_for_firm(self, firm_id: str) -> list[TotpEnrollment]: ...
