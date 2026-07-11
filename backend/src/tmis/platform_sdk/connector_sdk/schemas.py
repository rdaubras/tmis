from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ConnectorPage:
    items: tuple[dict[str, Any], ...]
    has_next: bool = False


@dataclass(frozen=True, slots=True)
class ConnectorResult:
    items: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
