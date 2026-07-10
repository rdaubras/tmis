import uuid
from datetime import UTC, datetime

from tmis.collaboration.approvals.ports import ApprovalStorePort
from tmis.collaboration.approvals.schemas import (
    ApprovalDecision,
    ApprovalDecisionType,
    ApprovalMode,
    ApprovalRequest,
    ApprovalStatus,
)


class ApprovalEngine:
    """Implements `ApprovalEnginePort` (see docs/38-guide-validations.md).

    Every decision is appended to `ApprovalRequest.history` and never
    overwritten; `status` is a derived, recomputed value — a rejection
    or a change request from any approver always overrides an approval,
    regardless of mode. In SINGLE mode, one APPROVE settles the request;
    in MULTIPLE mode, every listed approver must have APPROVE as their
    latest decision.
    """

    def __init__(self, store: ApprovalStorePort) -> None:
        self._store = store

    def request(
        self,
        workspace_id: str,
        target_type: str,
        target_id: str,
        requested_by: str,
        approver_ids: list[str],
        mode: ApprovalMode,
    ) -> ApprovalRequest:
        approval = ApprovalRequest(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            target_type=target_type,
            target_id=target_id,
            requested_by=requested_by,
            approver_ids=tuple(approver_ids),
            mode=mode,
            created_at=datetime.now(UTC),
        )
        self._store.save(approval)
        return approval

    def decide(
        self,
        approval_id: str,
        approver_id: str,
        decision: ApprovalDecisionType,
        comment: str | None = None,
    ) -> ApprovalRequest:
        approval = self._require(approval_id)
        if approver_id not in approval.approver_ids:
            raise ValueError(f"{approver_id!r} is not an approver for {approval_id!r}")
        approval.history.append(
            ApprovalDecision(
                approver_id=approver_id,
                decision=decision,
                comment=comment,
                decided_at=datetime.now(UTC),
            )
        )
        approval.status = self._compute_status(approval)
        self._store.save(approval)
        return approval

    def get(self, approval_id: str) -> ApprovalRequest:
        return self._require(approval_id)

    def list_for_target(self, target_type: str, target_id: str) -> list[ApprovalRequest]:
        return self._store.list_for_target(target_type, target_id)

    def _require(self, approval_id: str) -> ApprovalRequest:
        approval = self._store.get(approval_id)
        if approval is None:
            raise ValueError(f"Unknown approval request {approval_id!r}")
        return approval

    def _compute_status(self, approval: ApprovalRequest) -> ApprovalStatus:
        latest: dict[str, ApprovalDecisionType] = {}
        for entry in approval.history:
            latest[entry.approver_id] = entry.decision
        if any(d is ApprovalDecisionType.REJECT for d in latest.values()):
            return ApprovalStatus.REJECTED
        if any(d is ApprovalDecisionType.REQUEST_CHANGES for d in latest.values()):
            return ApprovalStatus.CHANGES_REQUESTED
        if approval.mode is ApprovalMode.SINGLE:
            if any(d is ApprovalDecisionType.APPROVE for d in latest.values()):
                return ApprovalStatus.APPROVED
            return ApprovalStatus.PENDING
        all_approved = all(
            latest.get(approver_id) is ApprovalDecisionType.APPROVE
            for approver_id in approval.approver_ids
        )
        return ApprovalStatus.APPROVED if all_approved else ApprovalStatus.PENDING
