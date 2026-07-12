from typing import Protocol

from tmis.integration_hub.conflict_resolution.schemas import (
    ConflictContext,
    ConflictResolution,
    ConflictStrategy,
)


class ConflictStrategyPort(Protocol):
    """One pluggable resolution policy for a data conflict between a
    locally held record and the record just read from an external
    system — "stratégies de résolution des conflits" (sprint
    requirement)."""

    strategy: ConflictStrategy

    def resolve(self, context: ConflictContext) -> ConflictResolution: ...
