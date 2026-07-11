from datetime import UTC, datetime

import structlog

from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus
from tmis.cabinet_knowledge.validation.ports import ValidationStorePort
from tmis.cabinet_knowledge.validation.schemas import (
    ValidationDecision,
    ValidationRequest,
    ValidationRequestStatus,
    new_validation_request_id,
)
from tmis.platform.metrics.bootstrap import get_metrics_registry

_logger = structlog.get_logger(__name__)


class ValidationEngine:
    """The human-in-the-loop workflow that stands between a knowledge
    object and the `VALIDATED` status — this is the module the sprint
    constraint "aucune connaissance ne peut être ajoutée
    automatiquement sans validation humaine" is enforced through:
    nothing in `cabinet_knowledge` can reach `VALIDATED` except via
    `decide(ValidationDecision.APPROVE, ...)`, called by a human
    reviewer."""

    def __init__(
        self,
        store: ValidationStorePort,
        knowledge_space: KnowledgeSpace,
        governance: GovernanceEngine,
    ) -> None:
        self._store = store
        self._knowledge_space = knowledge_space
        self._governance = governance

    def submit_for_validation(
        self, firm_id: str, knowledge_object_id: str, requested_by: str
    ) -> ValidationRequest:
        self._governance.transition(
            firm_id,
            knowledge_object_id,
            KnowledgeStatus.IN_REVIEW,
            actor=requested_by,
            reason="soumis pour validation",
        )
        request = ValidationRequest(
            id=new_validation_request_id(),
            firm_id=firm_id,
            knowledge_object_id=knowledge_object_id,
            requested_by=requested_by,
        )
        self._store.save(request)
        return request

    def decide(
        self,
        firm_id: str,
        request_id: str,
        decision: ValidationDecision,
        reviewer: str,
        comment: str | None = None,
    ) -> ValidationRequest:
        request = self._store.get(request_id)
        if request is None or request.firm_id != firm_id:
            raise KeyError(request_id)
        if request.status is not ValidationRequestStatus.PENDING:
            raise ValueError(f"Validation request {request_id} already decided")

        if decision is ValidationDecision.APPROVE:
            self._governance.transition(
                firm_id,
                request.knowledge_object_id,
                KnowledgeStatus.VALIDATED,
                actor=reviewer,
                reason=comment,
            )
            request.status = ValidationRequestStatus.APPROVED
        elif decision is ValidationDecision.REJECT:
            self._governance.transition(
                firm_id,
                request.knowledge_object_id,
                KnowledgeStatus.DRAFT,
                actor=reviewer,
                reason=comment,
            )
            request.status = ValidationRequestStatus.REJECTED
        else:
            self._governance.transition(
                firm_id,
                request.knowledge_object_id,
                KnowledgeStatus.DRAFT,
                actor=reviewer,
                reason=comment,
            )
            request.status = ValidationRequestStatus.CHANGES_REQUESTED

        request.reviewer = reviewer
        request.comment = comment
        request.decided_at = datetime.now(UTC)
        self._store.save(request)
        _logger.info(
            "cabinet_knowledge.validated",
            firm_id=firm_id,
            request_id=request_id,
            knowledge_object_id=request.knowledge_object_id,
            decision=decision.value,
            reviewer=reviewer,
        )
        get_metrics_registry().counter(
            "cabinet_knowledge_validations_total", "Total validation decisions"
        ).inc(decision=decision.value)
        return request

    def pending_for_firm(self, firm_id: str) -> list[ValidationRequest]:
        return self._store.pending_for_firm(firm_id)
