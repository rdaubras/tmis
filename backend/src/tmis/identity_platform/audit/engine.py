import dataclasses

from tmis.identity_platform.audit.ports import SecurityAuditStorePort
from tmis.identity_platform.audit.schemas import SecurityAuditEntry
from tmis.identity_platform.security_events.bus import SecurityEventBus
from tmis.identity_platform.security_events.schemas import SecurityEvent

_COMMON_FIELDS = frozenset({"firm_id", "event_id", "occurred_at"})


def _summarize(event: SecurityEvent) -> str:
    fields = {k: v for k, v in dataclasses.asdict(event).items() if k not in _COMMON_FIELDS}
    return ", ".join(f"{key}={value}" for key, value in fields.items())


class SecurityAuditEngine:
    """Subscribes to every `security_events.SecurityEvent` (via
    `SecurityEventBus.subscribe_all`) and builds an append-only,
    firm-scoped audit trail — "tous les événements de sécurité sont
    auditables" (sprint constraint). Never reimplements event
    publication; only observes it."""

    def __init__(self, store: SecurityAuditStorePort, bus: SecurityEventBus) -> None:
        self._store = store
        bus.subscribe_all(self._on_event)

    async def _on_event(self, event: SecurityEvent) -> None:
        self._store.append(
            SecurityAuditEntry(
                firm_id=event.firm_id,
                event_type=event.event_type,
                summary=_summarize(event),
                occurred_at=event.occurred_at,
            )
        )

    def list_for_firm(self, firm_id: str) -> list[SecurityAuditEntry]:
        return self._store.list_for_firm(firm_id)
