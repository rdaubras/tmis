import uuid
from datetime import UTC, datetime, timedelta

from tmis.cabinet_os.deadlines.ports import DeadlineRulePort, DeadlineStorePort
from tmis.cabinet_os.deadlines.schemas import Deadline, DeadlineStatus


class ConfigurableDeadlineEngine:
    """Implements `DeadlineEnginePort` (see docs/39-cabinet-os.md —
    Deadline Engine). Ships with **no rule registered by default** —
    computing deadlines from an event requires a `DeadlineRulePort`
    registered for that `procedure_type` first
    (`register_rule`); an unregistered procedure type simply computes
    nothing rather than raising, so adding new procedures/jurisdictions
    later never breaks existing callers."""

    def __init__(self, store: DeadlineStorePort) -> None:
        self._store = store
        self._rules: dict[str, DeadlineRulePort] = {}

    def register_rule(self, procedure_type: str, rule: DeadlineRulePort) -> None:
        self._rules[procedure_type] = rule

    def compute_from_event(
        self,
        firm_id: str,
        case_id: str,
        procedure_type: str,
        trigger_label: str,
        trigger_at: datetime,
    ) -> list[Deadline]:
        rule = self._rules.get(procedure_type)
        if rule is None:
            return []
        created: list[Deadline] = []
        for candidate in rule.compute(trigger_label, trigger_at):
            deadline = self.create(
                firm_id, case_id, candidate.label, candidate.due_at, candidate.alert_offsets
            )
            deadline.source_event_label = trigger_label
            self._store.save(deadline)
            created.append(deadline)
        return created

    def create(
        self,
        firm_id: str,
        case_id: str,
        label: str,
        due_at: datetime,
        alert_offsets: list[timedelta] | None = None,
    ) -> Deadline:
        deadline = Deadline(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            case_id=case_id,
            label=label,
            due_at=due_at,
            alert_offsets=list(alert_offsets or []),
            created_at=datetime.now(UTC),
        )
        self._store.save(deadline)
        return deadline

    def mark_done(self, deadline_id: str) -> Deadline:
        deadline = self._require(deadline_id)
        deadline.status = DeadlineStatus.DONE
        self._store.save(deadline)
        return deadline

    def mark_missed(self, deadline_id: str) -> Deadline:
        deadline = self._require(deadline_id)
        deadline.status = DeadlineStatus.MISSED
        self._store.save(deadline)
        return deadline

    def list_upcoming(self, firm_id: str, within: timedelta) -> list[Deadline]:
        now = datetime.now(UTC)
        horizon = now + within
        upcoming = [
            d
            for d in self._store.list_for_firm(firm_id)
            if d.status is DeadlineStatus.PENDING and now <= d.due_at <= horizon
        ]
        return sorted(upcoming, key=lambda d: d.due_at)

    def list_due_alerts(self, firm_id: str, now: datetime) -> list[Deadline]:
        due: list[Deadline] = []
        for deadline in self._store.list_for_firm(firm_id):
            if deadline.status is not DeadlineStatus.PENDING:
                continue
            for offset in deadline.alert_offsets:
                if deadline.due_at - offset <= now < deadline.due_at:
                    due.append(deadline)
                    break
        return due

    def _require(self, deadline_id: str) -> Deadline:
        deadline = self._store.get(deadline_id)
        if deadline is None:
            raise ValueError(f"Unknown deadline {deadline_id!r}")
        return deadline
