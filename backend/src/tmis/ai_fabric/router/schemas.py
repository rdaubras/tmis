from dataclasses import dataclass, field

from tmis.ai_fabric.model_profiles.schemas import ModelProfile
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor


@dataclass(frozen=True, slots=True)
class RoutingRequest:
    """The sprint's "ROUTER" input: task type, target cost, max time,
    quality level, subscription (firm), availability constraints, and
    the governance context (country/data type) needed by
    `tmis.ai_fabric.policies`."""

    firm_id: str
    task_type: str
    prompt: str
    profile: ModelProfile | None = None
    target_cost_usd: float | None = None
    max_latency_ms: float | None = None
    min_quality_score: float = 0.0
    country: str | None = None
    data_type: str | None = None


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    """A routing outcome plus the ordered, human-readable `reasons`
    that produced it — per the sprint's explicit requirement "le choix
    doit être explicable"."""

    model: ModelDescriptor
    reasons: tuple[str, ...] = field(default_factory=tuple)


class NoEligibleModelError(Exception):
    def __init__(self, request: RoutingRequest, reasons: tuple[str, ...]) -> None:
        super().__init__(
            f"No eligible model for task_type={request.task_type!r}: {'; '.join(reasons)}"
        )
        self.request = request
        self.reasons = reasons


class QuotaExceededError(Exception):
    def __init__(self, firm_id: str) -> None:
        super().__init__(f"AI Fabric quota exceeded for firm {firm_id!r}")
        self.firm_id = firm_id
