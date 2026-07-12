from datetime import UTC, datetime

from tmis.cloud_operations.incident_management.ports import (
    IncidentStorePort,
    IncidentUpdateStorePort,
)
from tmis.cloud_operations.incident_management.schemas import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    IncidentUpdate,
    PostMortemReport,
    new_incident_id,
    new_incident_update_id,
)


class UnknownIncidentError(KeyError):
    pass


class IncidentManagementEngine:
    """Incident lifecycle engine covering the four stages the sprint
    asks for ("ouverture, suivi, résolution, post-mortem")."""

    def __init__(self, incidents: IncidentStorePort, updates: IncidentUpdateStorePort) -> None:
        self._incidents = incidents
        self._updates = updates

    def open_incident(
        self,
        title: str,
        description: str,
        severity: IncidentSeverity,
        firm_id: str | None = None,
    ) -> Incident:
        incident = Incident(
            id=new_incident_id(),
            title=title,
            description=description,
            severity=severity,
            firm_id=firm_id,
        )
        self._incidents.save(incident)
        return incident

    def track(self, incident_id: str, message: str, author: str) -> IncidentUpdate:
        incident = self._incidents.get(incident_id)
        if incident is None:
            raise UnknownIncidentError(incident_id)
        if incident.status is IncidentStatus.OPEN:
            incident.status = IncidentStatus.INVESTIGATING
            self._incidents.save(incident)
        update = IncidentUpdate(
            id=new_incident_update_id(), incident_id=incident_id, message=message, author=author
        )
        self._updates.save(update)
        return update

    def resolve(self, incident_id: str) -> Incident:
        incident = self._incidents.get(incident_id)
        if incident is None:
            raise UnknownIncidentError(incident_id)
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.now(UTC)
        self._incidents.save(incident)
        return incident

    def record_post_mortem(
        self,
        incident_id: str,
        root_cause: str,
        impact: str,
        resolution: str,
        action_items: list[str],
    ) -> PostMortemReport:
        incident = self._incidents.get(incident_id)
        if incident is None:
            raise UnknownIncidentError(incident_id)
        incident.status = IncidentStatus.POST_MORTEM
        incident.post_mortem = root_cause
        self._incidents.save(incident)
        opened_at = incident.opened_at
        resolved_at = incident.resolved_at or datetime.now(UTC)
        duration_minutes = (resolved_at - opened_at).total_seconds() / 60.0
        return PostMortemReport(
            incident_id=incident.id,
            title=incident.title,
            severity=incident.severity,
            summary=incident.description,
            root_cause=root_cause,
            impact=impact,
            resolution=resolution,
            action_items=action_items,
            duration_minutes=duration_minutes,
        )

    def close(self, incident_id: str) -> Incident:
        incident = self._incidents.get(incident_id)
        if incident is None:
            raise UnknownIncidentError(incident_id)
        incident.status = IncidentStatus.CLOSED
        self._incidents.save(incident)
        return incident

    def timeline(self, incident_id: str) -> list[IncidentUpdate]:
        return self._updates.list_for_incident(incident_id)

    def open_incidents(self, firm_id: str | None = None) -> list[Incident]:
        return self._incidents.list_open(firm_id)
