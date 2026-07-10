from datetime import datetime, timedelta
from typing import Protocol

from tmis.cabinet_os.hearings.schemas import Hearing


class HearingStorePort(Protocol):
    def get(self, hearing_id: str) -> Hearing | None: ...

    def save(self, hearing: Hearing) -> None: ...

    def list_for_case(self, case_id: str) -> list[Hearing]: ...

    def list_for_firm(self, firm_id: str) -> list[Hearing]: ...


class HearingEnginePort(Protocol):
    """Port implemented by every interchangeable hearing engine."""

    def schedule(
        self,
        firm_id: str,
        case_id: str,
        jurisdiction: str,
        chamber: str,
        scheduled_at: datetime,
        *,
        room: str = "",
        participant_ids: set[str] | None = None,
        reminder_before: timedelta | None = timedelta(days=1),
    ) -> Hearing: ...

    def record_decision(self, hearing_id: str, decision: str) -> Hearing: ...

    def add_preparatory_document(self, hearing_id: str, document_id: str) -> Hearing: ...

    def list_for_case(self, case_id: str) -> list[Hearing]: ...
