from tmis.platform.disaster_recovery.schemas import FailoverDecision, RecoveryObjective


class DisasterRecoveryEngine:
    """Implements `DisasterRecoveryPort` (see
    docs/47-guide-securite-entreprise.md — Disaster Recovery). Owns
    the RTO/RPO targets and the heartbeat-threshold failover decision;
    the actual failover mechanics (DNS cutover, pod rescheduling) are
    infrastructure concerns handled by the Kubernetes manifests in
    `tmis.platform.kubernetes`, not by this engine."""

    def __init__(self, objective: RecoveryObjective) -> None:
        self._objective = objective

    def plan(self) -> RecoveryObjective:
        return self._objective

    def decide_failover(
        self, seconds_since_last_heartbeat: float, threshold_seconds: float
    ) -> FailoverDecision:
        if seconds_since_last_heartbeat <= threshold_seconds:
            return FailoverDecision(should_failover=False, reason="heartbeat within threshold")
        return FailoverDecision(
            should_failover=True,
            reason=(
                f"no heartbeat for {seconds_since_last_heartbeat:.0f}s "
                f"(threshold {threshold_seconds:.0f}s)"
            ),
        )
