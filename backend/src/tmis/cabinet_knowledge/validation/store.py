from tmis.cabinet_knowledge.validation.schemas import ValidationRequest, ValidationRequestStatus


class InMemoryValidationStore:
    def __init__(self) -> None:
        self._requests: dict[str, ValidationRequest] = {}

    def save(self, request: ValidationRequest) -> None:
        self._requests[request.id] = request

    def get(self, request_id: str) -> ValidationRequest | None:
        return self._requests.get(request_id)

    def pending_for_firm(self, firm_id: str) -> list[ValidationRequest]:
        return [
            r
            for r in self._requests.values()
            if r.firm_id == firm_id and r.status is ValidationRequestStatus.PENDING
        ]
