from tmis.workflow_automation.approval_gateway.schemas import ApprovalPolicy


class InMemoryApprovalPolicyStore:
    def __init__(self) -> None:
        self._policies: dict[tuple[str, str], ApprovalPolicy] = {}

    def set(self, policy: ApprovalPolicy) -> None:
        self._policies[(policy.firm_id, policy.action_type)] = policy

    def get(self, firm_id: str, action_type: str) -> ApprovalPolicy | None:
        return self._policies.get((firm_id, action_type))
