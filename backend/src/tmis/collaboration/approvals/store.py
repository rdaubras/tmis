from tmis.collaboration.approvals.schemas import ApprovalRequest


class InMemoryApprovalStore:
    """Implements `ApprovalStorePort` — reference implementation, swap
    for a persistent store without touching `ApprovalEngine`."""

    def __init__(self) -> None:
        self._approvals: dict[str, ApprovalRequest] = {}

    def get(self, approval_id: str) -> ApprovalRequest | None:
        return self._approvals.get(approval_id)

    def save(self, approval: ApprovalRequest) -> None:
        self._approvals[approval.id] = approval

    def list_for_workspace(self, workspace_id: str) -> list[ApprovalRequest]:
        return [a for a in self._approvals.values() if a.workspace_id == workspace_id]

    def list_for_target(self, target_type: str, target_id: str) -> list[ApprovalRequest]:
        return [
            a
            for a in self._approvals.values()
            if a.target_type == target_type and a.target_id == target_id
        ]
