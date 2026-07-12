from typing import Protocol

from tmis.integration_hub.connector_framework.schemas import ConnectorRecord
from tmis.integration_hub.synchronization.schemas import SyncJobConfig


class SyncJobStorePort(Protocol):
    def save(self, job: SyncJobConfig) -> None: ...

    def get(self, firm_id: str, job_id: str) -> SyncJobConfig | None: ...

    def list_all(self, firm_id: str) -> list[SyncJobConfig]: ...


class MapperPort(Protocol):
    """Decoupled input — structurally satisfied by
    `integration_hub.mapping` once it is built. `SynchronizationEngine`
    can be built and tested against a stub before `mapping` exists."""

    def map(self, record: ConnectorRecord, entity_type: str) -> ConnectorRecord: ...


class LocalRecordLookupPort(Protocol):
    """Decoupled input — the LIH does not own domain data, so the
    caller supplies whichever bounded context holds the local copy of
    `entity_type` (e.g. `cabinet_knowledge`, `case_intelligence`)."""

    def find(self, firm_id: str, entity_type: str, external_id: str) -> ConnectorRecord | None: ...
