import csv
import io

from tmis.ai_governance.audit.ports import AIAuditStorePort
from tmis.ai_governance.audit.schemas import AIAuditEntry, new_ai_audit_entry_id

_CSV_FIELDS = (
    "id",
    "production_id",
    "actor_id",
    "action",
    "prompt",
    "model_name",
    "cost_usd",
    "duration_ms",
    "decision_id",
    "policy_ids",
    "validation_id",
    "recorded_at",
)


class AIAuditEngine:
    """The sprint's "AI AUDIT": a specialized, append-only journal of
    everything that happened to produce and govern one AI output."""

    def __init__(self, store: AIAuditStorePort) -> None:
        self._store = store

    def record(
        self,
        firm_id: str,
        production_id: str,
        actor_id: str,
        action: str,
        *,
        prompt: str | None = None,
        model_name: str | None = None,
        cost_usd: float | None = None,
        duration_ms: float | None = None,
        decision_id: str | None = None,
        policy_ids: tuple[str, ...] = (),
        validation_id: str | None = None,
    ) -> AIAuditEntry:
        entry = AIAuditEntry(
            id=new_ai_audit_entry_id(),
            firm_id=firm_id,
            production_id=production_id,
            actor_id=actor_id,
            action=action,
            prompt=prompt,
            model_name=model_name,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            decision_id=decision_id,
            policy_ids=policy_ids,
            validation_id=validation_id,
        )
        self._store.add(entry)
        return entry

    def list_for_firm(self, firm_id: str) -> list[AIAuditEntry]:
        return self._store.list_for_firm(firm_id)

    def list_for_production(self, firm_id: str, production_id: str) -> list[AIAuditEntry]:
        return self._store.list_for_production(firm_id, production_id)

    def export_csv(self, firm_id: str) -> str:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for entry in self.list_for_firm(firm_id):
            writer.writerow(
                {
                    "id": entry.id,
                    "production_id": entry.production_id,
                    "actor_id": entry.actor_id,
                    "action": entry.action,
                    "prompt": entry.prompt or "",
                    "model_name": entry.model_name or "",
                    "cost_usd": entry.cost_usd if entry.cost_usd is not None else "",
                    "duration_ms": entry.duration_ms if entry.duration_ms is not None else "",
                    "decision_id": entry.decision_id or "",
                    "policy_ids": "|".join(entry.policy_ids),
                    "validation_id": entry.validation_id or "",
                    "recorded_at": entry.recorded_at.isoformat(),
                }
            )
        return buffer.getvalue()
