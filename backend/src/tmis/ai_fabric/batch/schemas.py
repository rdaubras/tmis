from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BatchRequest:
    request_id: str
    prompt: str
    model_name: str


@dataclass(frozen=True, slots=True)
class BatchResult:
    request_id: str
    text: str
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None
