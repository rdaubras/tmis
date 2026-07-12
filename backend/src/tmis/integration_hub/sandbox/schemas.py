from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ConnectorResourceQuota:
    max_calls_per_minute: int = 60
    max_execution_seconds: float = 10.0


@dataclass(frozen=True, slots=True)
class SandboxExecutionResult:
    connector_id: str
    success: bool
    result: Any | None = None
    error: str | None = None
    duration_seconds: float = 0.0
