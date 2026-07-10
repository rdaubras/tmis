from dataclasses import dataclass
from enum import Enum


class EnvironmentTier(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass(frozen=True, slots=True)
class ConfigIssue:
    """A Twelve-Factor config violation found by
    `validate_production_readiness` (see
    docs/47-guide-securite-entreprise.md — Configuration)."""

    field: str
    severity: str
    message: str
