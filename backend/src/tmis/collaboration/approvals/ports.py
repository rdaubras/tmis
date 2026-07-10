from typing import Protocol

from tmis.collaboration.approvals.schemas import (
    ApprovalDecisionType,
    ApprovalMode,
    ApprovalRequest,
)


class ApprovalStorePort(Protocol):
    def get(self, approval_id: str) -> ApprovalRequest | None: ...

    def save(self, approval: ApprovalRequest) -> None: ...

    def list_for_workspace(self, workspace_id: str) -> list[ApprovalRequest]: ...

    def list_for_target(self, target_type: str, target_id: str) -> list[ApprovalRequest]: ...


class ApprovalEnginePort(Protocol):
    """Port implemented by every interchangeable approval engine."""

    def request(
        self,
        workspace_id: str,
        target_type: str,
        target_id: str,
        requested_by: str,
        approver_ids: list[str],
        mode: ApprovalMode,
    ) -> ApprovalRequest: ...

    def decide(
        self,
        approval_id: str,
        approver_id: str,
        decision: ApprovalDecisionType,
        comment: str | None = None,
    ) -> ApprovalRequest: ...

    def get(self, approval_id: str) -> ApprovalRequest: ...

    def list_for_target(self, target_type: str, target_id: str) -> list[ApprovalRequest]: ...
