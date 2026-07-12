from typing import Protocol

from tmis.integration_hub.transformation.schemas import TransformKind


class TransformFunctionPort(Protocol):
    """One pluggable value transform, applied by `MappingEngine` to a
    field value while mapping a record — "les données transitant entre
    systèmes peuvent nécessiter des transformations de format" (sprint
    requirement)."""

    kind: TransformKind

    def apply(self, value: str) -> str: ...
