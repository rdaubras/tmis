from dataclasses import dataclass
from datetime import datetime

from tmis.cabinet_os.subscriptions.schemas import PlanTier

_PLAN_FEATURES: dict[PlanTier, frozenset[str]] = {
    PlanTier.SOLO: frozenset({"cases", "documents", "ai_assist"}),
    PlanTier.CABINET: frozenset({"cases", "documents", "ai_assist", "collaboration", "billing"}),
    PlanTier.ENTERPRISE: frozenset(
        {
            "cases",
            "documents",
            "ai_assist",
            "collaboration",
            "billing",
            "sso",
            "advanced_reporting",
            "audit_export",
        }
    ),
}

_PLAN_SEATS: dict[PlanTier, int] = {
    PlanTier.SOLO: 1,
    PlanTier.CABINET: 10,
    PlanTier.ENTERPRISE: 100,
}


def features_for_plan(plan: PlanTier) -> frozenset[str]:
    return _PLAN_FEATURES[plan]


def default_seats_for_plan(plan: PlanTier) -> int:
    return _PLAN_SEATS[plan]


@dataclass(slots=True)
class License:
    """A firm's license (see docs/47-guide-securite-entreprise.md —
    Licensing). `key` is the signed, tamper-evident license key handed
    to the firm; `LicenseEngine.validate` re-verifies its signature
    before trusting any of the other fields."""

    id: str
    firm_id: str
    plan: PlanTier
    seats: int
    features: frozenset[str]
    issued_at: datetime
    expires_at: datetime
    key: str
    renewed_at: datetime | None = None

    def is_expired(self, *, now: datetime | None = None) -> bool:
        return (now or datetime.now(self.expires_at.tzinfo)) > self.expires_at

    def has_feature(self, feature: str) -> bool:
        return feature in self.features


@dataclass(frozen=True, slots=True)
class LicenseValidationResult:
    valid: bool
    reason: str | None = None
