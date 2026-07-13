from tmis.legal_copilot_framework.validation_policies.schemas import CopilotValidationPolicy


class InMemoryCopilotValidationPolicyStore:
    def __init__(self) -> None:
        self._policies: dict[str, CopilotValidationPolicy] = {}

    def save(self, policy: CopilotValidationPolicy) -> None:
        self._policies[policy.id] = policy

    def get(self, policy_id: str) -> CopilotValidationPolicy | None:
        return self._policies.get(policy_id)

    def list_all(self) -> list[CopilotValidationPolicy]:
        return list(self._policies.values())
