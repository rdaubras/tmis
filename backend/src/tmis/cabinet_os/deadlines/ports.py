from datetime import datetime, timedelta
from typing import Protocol

from tmis.cabinet_os.deadlines.schemas import Deadline, DeadlineCandidate


class DeadlineRulePort(Protocol):
    """Extension point for procedure/jurisdiction-specific deadline
    computation — the Deadline Engine ships with no rule registered by
    default (see docs/39-cabinet-os.md — Deadline Engine); one is
    registered per `procedure_type` via
    `DeadlineEnginePort.register_rule`."""

    def compute(self, trigger_label: str, trigger_at: datetime) -> list[DeadlineCandidate]: ...


class DeadlineStorePort(Protocol):
    def get(self, deadline_id: str) -> Deadline | None: ...

    def save(self, deadline: Deadline) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[Deadline]: ...

    def list_for_case(self, case_id: str) -> list[Deadline]: ...


class DeadlineEnginePort(Protocol):
    """Port implemented by every interchangeable deadline engine."""

    def register_rule(self, procedure_type: str, rule: DeadlineRulePort) -> None: ...

    def compute_from_event(
        self,
        firm_id: str,
        case_id: str,
        procedure_type: str,
        trigger_label: str,
        trigger_at: datetime,
    ) -> list[Deadline]: ...

    def create(
        self,
        firm_id: str,
        case_id: str,
        label: str,
        due_at: datetime,
        alert_offsets: list[timedelta] | None = None,
    ) -> Deadline: ...

    def mark_done(self, deadline_id: str) -> Deadline: ...

    def mark_missed(self, deadline_id: str) -> Deadline: ...

    def list_upcoming(self, firm_id: str, within: timedelta) -> list[Deadline]: ...

    def list_due_alerts(self, firm_id: str, now: datetime) -> list[Deadline]: ...
