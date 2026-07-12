from datetime import UTC, datetime

from tmis.platform.backup.engine import BackupEngine
from tmis.platform.disaster_recovery.engine import DisasterRecoveryEngine
from tmis.platform.restore.engine import RestoreEngine
from tmis.runtime_platform.disaster_recovery.ports import BackupPolicyStorePort
from tmis.runtime_platform.disaster_recovery.schemas import (
    BackupPolicy,
    RestoreSimulationResult,
    RpoRtoEstimate,
)


class RuntimeDisasterRecoveryEngine:
    """Composes the three engines Sprint 10 already delivered
    (`BackupEngine`, `RestoreEngine`, `DisasterRecoveryEngine`)
    instead of a fourth backup implementation. Adds only what those
    three don't provide: a per-firm schedule/retention policy,
    restore simulation (dry-run + integrity check combined into one
    call), and an RPO/RTO estimate that compares the *actual* time
    since a firm's last backup against `DisasterRecoveryEngine.
    plan()`'s configured objective."""

    def __init__(
        self,
        backup: BackupEngine,
        restore: RestoreEngine,
        disaster_recovery: DisasterRecoveryEngine,
        policies: BackupPolicyStorePort,
    ) -> None:
        self._backup = backup
        self._restore = restore
        self._disaster_recovery = disaster_recovery
        self._policies = policies

    def set_policy(self, firm_id: str, schedule_cron: str, retention_days: int) -> BackupPolicy:
        policy = BackupPolicy(
            firm_id=firm_id, schedule_cron=schedule_cron, retention_days=retention_days
        )
        self._policies.save(policy)
        return policy

    def policy_for(self, firm_id: str) -> BackupPolicy | None:
        return self._policies.get(firm_id)

    def validate_backup(self, backup_id: str) -> bool:
        return self._backup.verify_integrity(backup_id)

    def simulate_restore(self, backup_id: str) -> RestoreSimulationResult:
        """A dry-run restore plan plus an integrity check, combined —
        `RestoreEngine.dry_run` alone tells an operator *what* would
        be restored but not whether the backup is intact enough to
        actually succeed."""
        plan = self._restore.dry_run(backup_id)
        return RestoreSimulationResult(
            backup_id=backup_id,
            plan=plan,
            integrity_valid=self.validate_backup(backup_id),
        )

    def estimate_rpo_rto(
        self, last_backup_at: datetime | None, *, now: datetime | None = None
    ) -> RpoRtoEstimate:
        now = now or datetime.now(UTC)
        objective = self._disaster_recovery.plan()
        if last_backup_at is None:
            return RpoRtoEstimate(
                rto_minutes=objective.rto_minutes,
                rpo_minutes=objective.rpo_minutes,
                actual_rpo_minutes=None,
                meets_objective=False,
            )
        actual_rpo_minutes = (now - last_backup_at).total_seconds() / 60
        return RpoRtoEstimate(
            rto_minutes=objective.rto_minutes,
            rpo_minutes=objective.rpo_minutes,
            actual_rpo_minutes=actual_rpo_minutes,
            meets_objective=actual_rpo_minutes <= objective.rpo_minutes,
        )
