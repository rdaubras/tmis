from typing import Protocol

from tmis.workflow_automation.approval_gateway.schemas import ApprovalPolicy


class ApprovalPolicyStorePort(Protocol):
    def set(self, policy: ApprovalPolicy) -> None: ...

    def get(self, firm_id: str, action_type: str) -> ApprovalPolicy | None: ...
