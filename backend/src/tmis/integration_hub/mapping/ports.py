from typing import Protocol

from tmis.integration_hub.mapping.schemas import MappingProfile


class MappingProfileStorePort(Protocol):
    def save(self, profile: MappingProfile) -> None: ...

    def get(self, firm_id: str, connector_id: str, entity_type: str) -> MappingProfile | None: ...


class TransformerPort(Protocol):
    """Decoupled input — structurally satisfied by
    `transformation.engine.TransformationEngine` so `MappingEngine`
    can be built and tested independently of `transformation`."""

    def apply(self, transform_id: str, value: str) -> str: ...
