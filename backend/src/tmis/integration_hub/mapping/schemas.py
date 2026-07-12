from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FieldMapping:
    source_field: str
    target_field: str
    transform_id: str | None = None


@dataclass(slots=True)
class MappingProfile:
    """The field mapping between one connector's external schema and
    a TMIS entity type, for one firm — "le mapping des champs entre
    systèmes est entièrement configurable" (sprint requirement)."""

    id: str
    connector_id: str
    firm_id: str
    entity_type: str
    fields: tuple[FieldMapping, ...] = ()
