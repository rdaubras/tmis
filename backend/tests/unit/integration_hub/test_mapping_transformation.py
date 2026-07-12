import pytest

from tmis.integration_hub.connector_framework import ConnectorRecord
from tmis.integration_hub.mapping import (
    ConnectorMapper,
    FieldMapping,
    InMemoryMappingProfileStore,
    MappingEngine,
    MappingProfile,
)
from tmis.integration_hub.transformation import (
    TransformationEngine,
    TransformKind,
    UnknownTransformError,
)


def test_transformation_engine_default_transforms() -> None:
    engine = TransformationEngine()
    assert engine.apply("uppercase", "abc") == "ABC"
    assert engine.apply("lowercase", "ABC") == "abc"
    assert engine.apply("trim", "  x  ") == "x"
    assert engine.apply("date_iso", "25/12/2023") == "2023-12-25"


def test_transformation_engine_date_iso_passthrough_on_unparseable() -> None:
    engine = TransformationEngine()
    assert engine.apply("date_iso", "not-a-date") == "not-a-date"


def test_transformation_engine_unknown_transform_raises() -> None:
    engine = TransformationEngine()
    with pytest.raises((UnknownTransformError, ValueError)):
        engine.apply("unknown-transform", "x")


def test_transformation_engine_register_custom_transform() -> None:
    engine = TransformationEngine()

    class ReverseTransform:
        kind = TransformKind.UPPERCASE

        def apply(self, value: str) -> str:
            return value[::-1]

    engine.register(ReverseTransform())
    assert engine.apply("uppercase", "abc") == "cba"


def test_mapping_engine_maps_fields_with_transform() -> None:
    store = InMemoryMappingProfileStore()
    store.save(
        MappingProfile(
            id="mp-1",
            connector_id="c1",
            firm_id="f1",
            entity_type="client",
            fields=(
                FieldMapping(source_field="Nom", target_field="name", transform_id="uppercase"),
                FieldMapping(source_field="Ignored", target_field="ignored"),
            ),
        )
    )
    engine = MappingEngine(store, TransformationEngine())
    record = ConnectorRecord(external_id="e1", data={"Nom": "dupont"})

    mapped = engine.map(record, "client", connector_id="c1", firm_id="f1")
    assert mapped.data == {"name": "DUPONT"}
    assert mapped.external_id == "e1"


def test_mapping_engine_no_profile_passes_through() -> None:
    store = InMemoryMappingProfileStore()
    engine = MappingEngine(store)
    record = ConnectorRecord(external_id="e1", data={"raw": "value"})
    mapped = engine.map(record, "client", connector_id="unknown", firm_id="f1")
    assert mapped is record


def test_connector_mapper_binds_connector_and_firm() -> None:
    store = InMemoryMappingProfileStore()
    store.save(
        MappingProfile(
            id="mp-1", connector_id="c1", firm_id="f1", entity_type="client",
            fields=(FieldMapping(source_field="x", target_field="y"),),
        )
    )
    engine = MappingEngine(store)
    mapper = ConnectorMapper(engine, connector_id="c1", firm_id="f1")
    record = ConnectorRecord(external_id="e1", data={"x": "1"})
    mapped = mapper.map(record, "client")
    assert mapped.data == {"y": "1"}
