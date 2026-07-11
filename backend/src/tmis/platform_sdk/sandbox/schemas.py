from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ResourceQuota:
    max_calls_per_minute: int = 60
    max_execution_seconds: float = 5.0


@dataclass(frozen=True, slots=True)
class SandboxExecutionResult:
    plugin_id: str
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None
    duration_seconds: float = 0.0
