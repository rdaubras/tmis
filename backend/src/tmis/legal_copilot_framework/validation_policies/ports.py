from typing import Protocol

from tmis.legal_copilot_framework.validation_policies.schemas import CopilotValidationPolicy


class CopilotValidationPolicyStorePort(Protocol):
    def save(self, policy: CopilotValidationPolicy) -> None: ...

    def get(self, policy_id: str) -> CopilotValidationPolicy | None: ...

    def list_all(self) -> list[CopilotValidationPolicy]: ...
