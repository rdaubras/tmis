from tmis.ai_fabric.token_manager.engine import TokenManager
from tmis.business_platform.metering.ports import MeteringEventStorePort
from tmis.business_platform.metering.schemas import MeteredDimension, MeteringEvent, new_event_id


class MeteringEngine:
    """Historized usage metering across the seven signals the sprint
    asks for. AI calls/tokens compose `ai_fabric.token_manager.
    TokenManager` (itself composing `platform.cost_control.
    CostTrackerEngine`, Sprint 10/14) directly — never a second cost
    bookkeeping system — and are also logged as `MeteringEvent`s here
    so every dimension shares one historized, cross-cutting event
    log rather than five separate counters."""

    def __init__(self, store: MeteringEventStorePort, token_manager: TokenManager) -> None:
        self._store = store
        self._token_manager = token_manager

    def record(
        self,
        firm_id: str,
        dimension: MeteredDimension,
        quantity: float,
        metadata: dict[str, str] | None = None,
    ) -> MeteringEvent:
        event = MeteringEvent(
            id=new_event_id(),
            firm_id=firm_id,
            dimension=dimension,
            quantity=quantity,
            metadata=metadata or {},
        )
        self._store.save(event)
        return event

    def record_ai_call(
        self,
        firm_id: str,
        user_id: str,
        provider: str,
        model: str,
        prompt: str,
        response_text: str,
        *,
        cache_hit: bool = False,
        case_id: str | None = None,
        workflow_id: str | None = None,
    ) -> MeteringEvent:
        cost_entry = self._token_manager.record_usage(
            firm_id,
            user_id,
            provider,
            model,
            prompt,
            response_text,
            cache_hit=cache_hit,
            case_id=case_id,
            workflow_id=workflow_id,
        )
        self.record(firm_id, MeteredDimension.AI_CALLS, 1, {"provider": provider, "model": model})
        return self.record(
            firm_id,
            MeteredDimension.TOKENS,
            cost_entry.token_count,
            {"provider": provider, "model": model},
        )

    def total_for_dimension(self, firm_id: str, dimension: MeteredDimension) -> float:
        return sum(e.quantity for e in self._store.list_for_firm(firm_id, dimension))

    def history_for_firm(self, firm_id: str) -> list[MeteringEvent]:
        return self._store.list_for_firm(firm_id)

    def cache_hit_rate(self, firm_id: str) -> float:
        return self._token_manager.cache_hit_rate(firm_id)
