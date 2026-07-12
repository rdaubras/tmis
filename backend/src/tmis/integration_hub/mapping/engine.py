from tmis.integration_hub.connector_framework.schemas import ConnectorRecord
from tmis.integration_hub.mapping.ports import MappingProfileStorePort, TransformerPort


class MappingEngine:
    """Implements `synchronization.ports.MapperPort` (once bound to a
    connector/firm via `ConnectorMapper`) by applying a firm's
    configured `MappingProfile` — records with no configured profile
    pass through unchanged rather than being dropped."""

    def __init__(
        self, store: MappingProfileStorePort, transformer: TransformerPort | None = None
    ) -> None:
        self._store = store
        self._transformer = transformer

    def map(
        self, record: ConnectorRecord, entity_type: str, *, connector_id: str, firm_id: str
    ) -> ConnectorRecord:
        profile = self._store.get(firm_id, connector_id, entity_type)
        if profile is None:
            return record

        mapped_data: dict[str, str] = {}
        for field_mapping in profile.fields:
            if field_mapping.source_field not in record.data:
                continue
            value = record.data[field_mapping.source_field]
            if field_mapping.transform_id is not None and self._transformer is not None:
                value = self._transformer.apply(field_mapping.transform_id, value)
            mapped_data[field_mapping.target_field] = value

        return ConnectorRecord(
            external_id=record.external_id, data=mapped_data, updated_at=record.updated_at
        )


class ConnectorMapper:
    """Binds a `MappingEngine` to one connector/firm pair, adapting it
    to the narrow `synchronization.ports.MapperPort` shape."""

    def __init__(self, engine: MappingEngine, connector_id: str, firm_id: str) -> None:
        self._engine = engine
        self._connector_id = connector_id
        self._firm_id = firm_id

    def map(self, record: ConnectorRecord, entity_type: str) -> ConnectorRecord:
        return self._engine.map(
            record, entity_type, connector_id=self._connector_id, firm_id=self._firm_id
        )
