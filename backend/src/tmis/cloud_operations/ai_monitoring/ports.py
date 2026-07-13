from typing import Protocol

from tmis.cloud_operations.ai_monitoring.schemas import AIQualityIncident


class AIQualityIncidentStorePort(Protocol):
    def save(self, incident: AIQualityIncident) -> None: ...

    def list_recent(self, limit: int) -> list[AIQualityIncident]: ...
