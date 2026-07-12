from dataclasses import dataclass
from enum import StrEnum


class QuotaDimension(StrEnum):
    """The seven dimensions the sprint asks for — "utilisateurs,
    stockage, appels IA, temps GPU, nombre de dossiers, nombre de
    workflows, nombre d'agents"."""

    USERS = "users"
    STORAGE_GB = "storage_gb"
    AI_CALLS = "ai_calls"
    GPU_MINUTES = "gpu_minutes"
    CASES = "cases"
    WORKFLOWS = "workflows"
    AGENTS = "agents"


@dataclass(frozen=True, slots=True)
class QuotaOverride:
    """An option-driven increase on top of a plan's base limit for one
    dimension — "les quotas peuvent être augmentés par option" (sprint
    requirement). Additive: the effective limit is always
    `plan_limit + extra_amount`, never a replacement, so raising an
    option can never accidentally lower what the plan already grants.
    """

    firm_id: str
    dimension: QuotaDimension
    extra_amount: int


@dataclass(frozen=True, slots=True)
class QuotaCheckResult:
    dimension: QuotaDimension
    limit: int
    used: int
    allowed: bool
