from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Quota:
    scope: str
    scope_id: str
    max_calls_per_period: int
    period_days: int
