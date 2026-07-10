from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecoveryObjective:
    """RTO/RPO targets for a deployment tier (see
    docs/47-guide-securite-entreprise.md — Disaster Recovery)."""

    rto_minutes: int
    rpo_minutes: int


@dataclass(frozen=True, slots=True)
class FailoverDecision:
    should_failover: bool
    reason: str
