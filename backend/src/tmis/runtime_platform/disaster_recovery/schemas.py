from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.platform.restore.schemas import RestorePlan


@dataclass(slots=True)
class BackupPolicy:
    """A firm's backup schedule and retention — the piece `platform.
    backup.BackupEngine` (Sprint 10) never modeled: it can create a
    backup when asked, but nothing in TMIS previously recorded *how
    often* it should be asked, or *how long* a backup should be kept."""

    firm_id: str
    schedule_cron: str
    retention_days: int


@dataclass(frozen=True, slots=True)
class RestoreSimulationResult:
    backup_id: str
    plan: RestorePlan
    integrity_valid: bool
    simulated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class RpoRtoEstimate:
    rto_minutes: int
    rpo_minutes: int
    actual_rpo_minutes: float | None
    meets_objective: bool
    estimated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
