from functools import lru_cache

from tmis.platform.disaster_recovery.engine import DisasterRecoveryEngine
from tmis.platform.disaster_recovery.schemas import RecoveryObjective

_DEFAULT_OBJECTIVE = RecoveryObjective(rto_minutes=60, rpo_minutes=15)


@lru_cache
def get_disaster_recovery_engine() -> DisasterRecoveryEngine:
    """Process-wide `DisasterRecoveryEngine` singleton — see
    docs/47-guide-securite-entreprise.md. Default targets (RTO 60min,
    RPO 15min) are conservative starting points for a pilot deployment
    and should be revisited per-tier once real infrastructure SLAs are
    established."""
    return DisasterRecoveryEngine(_DEFAULT_OBJECTIVE)
