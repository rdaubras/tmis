from tmis.ai_governance.human_validation.ports import ValidationStorePort
from tmis.ai_governance.human_validation.schemas import (
    ValidationDecisionEntry,
    ValidationDecisionType,
    ValidationMode,
    ValidationRequest,
    ValidationStatus,
    new_validation_request_id,
)


def _tier_is_approved(
    tier_approver_ids: tuple[str, ...],
    tier_index: int,
    history: list[ValidationDecisionEntry],
    mode: ValidationMode,
) -> bool:
    tier_approvals = {
        entry.approver_id
        for entry in history
        if entry.tier == tier_index and entry.decision is ValidationDecisionType.APPROVE
    }
    if mode is ValidationMode.MULTIPLE:
        return set(tier_approver_ids) <= tier_approvals
    return len(tier_approvals) > 0


def _recompute_status(request: ValidationRequest) -> ValidationStatus:
    if any(e.decision is ValidationDecisionType.REJECT for e in request.history):
        return ValidationStatus.REJECTED
    if any(e.decision is ValidationDecisionType.REQUEST_REVISION for e in request.history):
        return ValidationStatus.REVISION_REQUESTED
    for tier_index, tier_approvers in enumerate(request.approver_tiers):
        if not _tier_is_approved(tier_approvers, tier_index, request.history, request.mode):
            return ValidationStatus.PENDING
    return ValidationStatus.APPROVED


def _current_tier_index(request: ValidationRequest) -> int:
    for tier_index, tier_approvers in enumerate(request.approver_tiers):
        if not _tier_is_approved(tier_approvers, tier_index, request.history, request.mode):
            return tier_index
    return max(0, len(request.approver_tiers) - 1)


class HumanValidationEngine:
    """The sprint's "HUMAN VALIDATION": simple, multiple, and
    hierarchical validation, plus reject and request-revision — all
    historized, never overwritten. HIERARCHICAL is the one mode with
    no precedent elsewhere in TMIS (`tmis.collaboration.approvals`
    only has SINGLE/MULTIPLE): each tier needs at least one approval
    from within that tier before the next tier is considered, mirroring
    a typical sign-off chain (associate → partner → managing partner)."""

    def __init__(self, store: ValidationStorePort) -> None:
        self._store = store

    def request_simple(
        self, firm_id: str, production_id: str, requested_by: str, approver_ids: tuple[str, ...]
    ) -> ValidationRequest:
        return self._request(
            firm_id, production_id, requested_by, (approver_ids,), ValidationMode.SIMPLE
        )

    def request_multiple(
        self, firm_id: str, production_id: str, requested_by: str, approver_ids: tuple[str, ...]
    ) -> ValidationRequest:
        return self._request(
            firm_id, production_id, requested_by, (approver_ids,), ValidationMode.MULTIPLE
        )

    def request_hierarchical(
        self,
        firm_id: str,
        production_id: str,
        requested_by: str,
        approver_tiers: tuple[tuple[str, ...], ...],
    ) -> ValidationRequest:
        return self._request(
            firm_id, production_id, requested_by, approver_tiers, ValidationMode.HIERARCHICAL
        )

    def _request(
        self,
        firm_id: str,
        production_id: str,
        requested_by: str,
        approver_tiers: tuple[tuple[str, ...], ...],
        mode: ValidationMode,
    ) -> ValidationRequest:
        request = ValidationRequest(
            id=new_validation_request_id(),
            firm_id=firm_id,
            production_id=production_id,
            requested_by=requested_by,
            approver_tiers=approver_tiers,
            mode=mode,
        )
        self._store.save(request)
        return request

    def decide(
        self,
        firm_id: str,
        request_id: str,
        approver_id: str,
        decision: ValidationDecisionType,
        comment: str | None = None,
    ) -> ValidationRequest:
        request = self._store.get(firm_id, request_id)
        if request is None:
            raise KeyError(f"validation request {request_id} not found for firm {firm_id}")

        tier = _current_tier_index(request)
        request.history.append(
            ValidationDecisionEntry(
                approver_id=approver_id, decision=decision, tier=tier, comment=comment
            )
        )
        request.status = _recompute_status(request)
        self._store.save(request)
        return request

    def history(self, firm_id: str, production_id: str) -> list[ValidationRequest]:
        return self._store.list_for_production(firm_id, production_id)

    def is_validated(self, firm_id: str, production_id: str) -> bool:
        requests = self.history(firm_id, production_id)
        return any(r.status is ValidationStatus.APPROVED for r in requests)
