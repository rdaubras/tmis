from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class IdentityDashboard:
    """Firm-wide identity & trust posture snapshot — "tableaux de
    bord : connexions, MFA, appareils, délégations, politiques,
    risques, sessions, authentifications, événements de sécurité"
    (sprint requirement). A genuinely new dashboard, distinct from
    `platform.monitoring.SupervisionDashboard` (Sprint 10, platform
    health + cost) — this one is identity-specific."""

    firm_id: str
    active_sessions: int
    mfa_enrolled_users: int
    trusted_devices: int
    active_delegations: int
    active_policies: int
    security_events_total: int
    high_risk_events_last_24h: int
    computed_at: datetime

    @staticmethod
    def now() -> datetime:
        return datetime.now(UTC)
