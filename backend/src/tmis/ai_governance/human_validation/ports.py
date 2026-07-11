from typing import Protocol

from tmis.ai_governance.human_validation.schemas import ValidationRequest


class ValidationStorePort(Protocol):
    def save(self, request: ValidationRequest) -> None: ...

    def get(self, firm_id: str, request_id: str) -> ValidationRequest | None: ...

    def list_for_production(
        self, firm_id: str, production_id: str
    ) -> list[ValidationRequest]: ...
