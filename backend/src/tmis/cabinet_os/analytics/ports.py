from typing import Protocol

from tmis.cabinet_os.analytics.schemas import FirmAnalytics


class AIUsagePort(Protocol):
    """Narrow read-only port into the AI Kernel's usage (see
    docs/39-cabinet-os.md — constraints): `cabinet_os` depends on
    `tmis.ai` only through a port like this one, consuming the Kernel's
    own evaluator rather than a model provider or connector directly.
    """

    def total_requests(self, firm_id: str) -> int: ...


class AnalyticsEnginePort(Protocol):
    """Port implemented by every interchangeable analytics engine."""

    def compute_firm_analytics(self, firm_id: str) -> FirmAnalytics: ...
