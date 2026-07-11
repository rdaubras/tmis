from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.cost_control.schemas import CostEntry


def estimate_tokens(text: str) -> int:
    """A word-count heuristic, consistent with the estimate
    `tmis.ai.providers` stubs already use for `ModelResponse.
    prompt_tokens` (Sprint 2) — not a real tokenizer, since none of
    the providers wired so far make a real network call either."""
    return max(1, len(text.split()))


class TokenManager:
    """The sprint's "TOKEN MANAGER" spec: tokens, coût, cache,
    consommation par cabinet, consommation par workflow — a thin
    wrapper around `tmis.platform.cost_control.CostTrackerEngine`
    (Sprint 10), which already tracks per-firm/case/workflow AI cost;
    this module adds token estimation on top rather than
    reimplementing per-firm cost bookkeeping."""

    def __init__(self, cost_tracker: CostTrackerEngine) -> None:
        self._cost_tracker = cost_tracker

    def record_usage(
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
    ) -> CostEntry:
        token_count = estimate_tokens(prompt) + estimate_tokens(response_text)
        return self._cost_tracker.record(
            firm_id,
            user_id,
            provider,
            model,
            token_count,
            case_id=case_id,
            workflow_id=workflow_id,
            cache_hit=cache_hit,
        )

    def consumption_by_workflow(self, workflow_id: str) -> float:
        return self._cost_tracker.cost_by_workflow(workflow_id)

    def cache_hit_rate(self, firm_id: str) -> float:
        return self._cost_tracker.cache_hit_rate(firm_id)
