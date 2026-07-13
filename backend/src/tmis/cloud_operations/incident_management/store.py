from tmis.cloud_operations.incident_management.schemas import (
    Incident,
    IncidentStatus,
    IncidentUpdate,
)


class InMemoryIncidentStore:
    def __init__(self) -> None:
        self._incidents: dict[str, Incident] = {}

    def save(self, incident: Incident) -> None:
        self._incidents[incident.id] = incident

    def get(self, incident_id: str) -> Incident | None:
        return self._incidents.get(incident_id)

    def list_open(self, firm_id: str | None = None) -> list[Incident]:
        closed = {IncidentStatus.RESOLVED, IncidentStatus.POST_MORTEM, IncidentStatus.CLOSED}
        return [
            i
            for i in self._incidents.values()
            if i.status not in closed and (firm_id is None or i.firm_id == firm_id)
        ]

    def list_all(self, firm_id: str | None = None) -> list[Incident]:
        return [i for i in self._incidents.values() if firm_id is None or i.firm_id == firm_id]


class InMemoryIncidentUpdateStore:
    def __init__(self) -> None:
        self._updates: list[IncidentUpdate] = []

    def save(self, update: IncidentUpdate) -> None:
        self._updates.append(update)

    def list_for_incident(self, incident_id: str) -> list[IncidentUpdate]:
        return [u for u in self._updates if u.incident_id == incident_id]
