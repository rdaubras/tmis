from tmis.ai_governance.human_validation.schemas import ValidationRequest


class InMemoryValidationStore:
    def __init__(self) -> None:
        self._requests: dict[str, ValidationRequest] = {}

    def save(self, request: ValidationRequest) -> None:
        self._requests[request.id] = request

    def get(self, firm_id: str, request_id: str) -> ValidationRequest | None:
        request = self._requests.get(request_id)
        if request is None or request.firm_id != firm_id:
            return None
        return request

    def list_for_production(self, firm_id: str, production_id: str) -> list[ValidationRequest]:
        return [
            r
            for r in self._requests.values()
            if r.firm_id == firm_id and r.production_id == production_id
        ]
