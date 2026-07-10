from dataclasses import dataclass
from enum import Enum


class DeploymentTier(str, Enum):
    """The four deployment sizes TMIS must scale across without a
    major redesign (see docs/47-guide-securite-entreprise.md —
    Enterprise Architecture): a solo lawyer, a 10-person cabinet, a
    100-user cabinet, and a corporate legal department."""

    SOLO = "solo"
    CABINET_SMALL = "cabinet_small"
    CABINET_LARGE = "cabinet_large"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True, slots=True)
class DeploymentProfile:
    tier: DeploymentTier
    replicas: int
    cpu_request: str
    cpu_limit: str
    memory_request: str
    memory_limit: str
    max_ai_concurrency: int
