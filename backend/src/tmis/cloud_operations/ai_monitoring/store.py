from tmis.cloud_operations.ai_monitoring.schemas import AIQualityIncident


class InMemoryAIQualityIncidentStore:
    def __init__(self) -> None:
        self._incidents: list[AIQualityIncident] = []

    def save(self, incident: AIQualityIncident) -> None:
        self._incidents.append(incident)

    def list_recent(self, limit: int) -> list[AIQualityIncident]:
        return list(reversed(self._incidents))[:limit]
