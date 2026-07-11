from typing import Protocol

from tmis.cabinet_knowledge.validation.schemas import ValidationRequest


class ValidationStorePort(Protocol):
    def save(self, request: ValidationRequest) -> None: ...

    def get(self, request_id: str) -> ValidationRequest | None: ...

    def pending_for_firm(self, firm_id: str) -> list[ValidationRequest]: ...
