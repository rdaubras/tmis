from tmis.ai_governance.traceability.ports import TraceStorePort
from tmis.ai_governance.traceability.schemas import TraceEntry, TraceEntryKind, new_trace_entry_id


class TraceabilityEngine:
    """The sprint's "TRACEABILITY ENGINE": a complete, append-only
    chain of every element that went into one AI production. One
    convenience method per traced kind, all delegating to `record()`,
    so the full chain is always queryable in one call."""

    def __init__(self, store: TraceStorePort) -> None:
        self._store = store

    def record(
        self, firm_id: str, production_id: str, kind: TraceEntryKind, reference: str, detail: str
    ) -> TraceEntry:
        entry = TraceEntry(
            id=new_trace_entry_id(),
            firm_id=firm_id,
            production_id=production_id,
            kind=kind,
            reference=reference,
            detail=detail,
        )
        self._store.add(entry)
        return entry

    def record_user(self, firm_id: str, production_id: str, user_id: str) -> TraceEntry:
        return self.record(
            firm_id, production_id, TraceEntryKind.USER, user_id, f"utilisateur {user_id}"
        )

    def record_case(self, firm_id: str, production_id: str, case_id: str) -> TraceEntry:
        return self.record(
            firm_id, production_id, TraceEntryKind.CASE, case_id, f"dossier {case_id}"
        )

    def record_model_version(
        self, firm_id: str, production_id: str, model_name: str, version: str
    ) -> TraceEntry:
        reference = f"{model_name}@{version}"
        return self.record(
            firm_id,
            production_id,
            TraceEntryKind.MODEL_VERSION,
            reference,
            f"modèle {model_name} version {version}",
        )

    def record_prompt(self, firm_id: str, production_id: str, prompt_id: str) -> TraceEntry:
        return self.record(
            firm_id, production_id, TraceEntryKind.PROMPT, prompt_id, f"prompt {prompt_id}"
        )

    def record_intermediate_response(
        self, firm_id: str, production_id: str, response_id: str, summary: str
    ) -> TraceEntry:
        return self.record(
            firm_id, production_id, TraceEntryKind.INTERMEDIATE_RESPONSE, response_id, summary
        )

    def record_human_validation(
        self, firm_id: str, production_id: str, validation_id: str, outcome: str
    ) -> TraceEntry:
        return self.record(
            firm_id, production_id, TraceEntryKind.HUMAN_VALIDATION, validation_id, outcome
        )

    def record_final_decision(
        self, firm_id: str, production_id: str, decision_id: str, summary: str
    ) -> TraceEntry:
        return self.record(
            firm_id, production_id, TraceEntryKind.FINAL_DECISION, decision_id, summary
        )

    def trace(self, firm_id: str, production_id: str) -> list[TraceEntry]:
        return self._store.list_for_production(firm_id, production_id)
