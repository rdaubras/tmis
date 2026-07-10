from typing import Protocol

from tmis.platform.disaster_recovery.schemas import FailoverDecision, RecoveryObjective


class DisasterRecoveryPort(Protocol):
    """Port implemented by every interchangeable disaster-recovery
    coordinator."""

    def plan(self) -> RecoveryObjective: ...

    def decide_failover(
        self, seconds_since_last_heartbeat: float, threshold_seconds: float
    ) -> FailoverDecision: ...
