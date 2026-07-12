from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.integration_hub.conflict_resolution.schemas import (
    ConflictContext,
    ConflictResolution,
    ConflictStrategy,
)


class LocalWinsStrategy:
    strategy = ConflictStrategy.LOCAL_WINS

    def resolve(self, context: ConflictContext) -> ConflictResolution:
        return ConflictResolution(
            resolved_record=context.local_record,
            strategy_used=self.strategy,
            detail="Enregistrement local conservé",
        )


class RemoteWinsStrategy:
    strategy = ConflictStrategy.REMOTE_WINS

    def resolve(self, context: ConflictContext) -> ConflictResolution:
        return ConflictResolution(
            resolved_record=context.remote_record,
            strategy_used=self.strategy,
            detail="Enregistrement distant retenu",
        )


class LastWriteWinsStrategy:
    strategy = ConflictStrategy.LAST_WRITE_WINS

    def resolve(self, context: ConflictContext) -> ConflictResolution:
        local_ts = context.local_record.updated_at
        remote_ts = context.remote_record.updated_at
        if local_ts is not None and (remote_ts is None or local_ts >= remote_ts):
            return ConflictResolution(
                resolved_record=context.local_record,
                strategy_used=self.strategy,
                detail="Enregistrement local plus récent",
            )
        return ConflictResolution(
            resolved_record=context.remote_record,
            strategy_used=self.strategy,
            detail="Enregistrement distant plus récent",
        )


class HumanValidationStrategy:
    """Defers to `ai_governance.human_validation` — the LIH never
    reimplements an approval workflow, it composes the one TMIS
    already has (same reuse already applied by
    `strategic_intelligence.review` and
    `workflow_automation.approval_gateway`)."""

    strategy = ConflictStrategy.HUMAN_VALIDATION

    def __init__(
        self, validation_engine: HumanValidationEngine, approver_ids: tuple[str, ...]
    ) -> None:
        self._validation_engine = validation_engine
        self._approver_ids = approver_ids

    def resolve(self, context: ConflictContext) -> ConflictResolution:
        production_id = f"{context.connector_id}:{context.external_id}"
        if self._validation_engine.is_validated(context.firm_id, production_id):
            return ConflictResolution(
                resolved_record=context.remote_record,
                strategy_used=self.strategy,
                detail="Validé par un humain — enregistrement distant retenu",
            )
        if not self._validation_engine.history(context.firm_id, production_id):
            self._validation_engine.request_simple(
                context.firm_id, production_id, "integration_hub", self._approver_ids
            )
        return ConflictResolution(
            resolved_record=None,
            strategy_used=self.strategy,
            pending_human_validation=True,
            detail="En attente de validation humaine",
        )


def default_strategies() -> tuple[LocalWinsStrategy, RemoteWinsStrategy, LastWriteWinsStrategy]:
    return (LocalWinsStrategy(), RemoteWinsStrategy(), LastWriteWinsStrategy())
