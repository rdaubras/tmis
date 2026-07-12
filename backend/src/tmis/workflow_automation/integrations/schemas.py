from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class IntegrationResult:
    success: bool
    detail: str
    output: dict[str, str] = field(default_factory=dict)
