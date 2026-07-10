from datetime import UTC, datetime

from tmis.cabinet_os.analytics.ports import AIUsagePort
from tmis.cabinet_os.analytics.schemas import FirmAnalytics
from tmis.cabinet_os.clients.ports import ClientStorePort
from tmis.cabinet_os.clients.schemas import ClientStatus
from tmis.cabinet_os.documents.ports import CabinetDocumentStorePort
from tmis.cabinet_os.time_tracking.ports import TimeEntryStorePort


class AnalyticsEngine:
    """Implements `AnalyticsEnginePort` (see docs/39-cabinet-os.md —
    Analytics Engine): composes the read ports of other `cabinet_os`
    modules and, for AI usage, the narrow `AIUsagePort` into the
    Kernel — it never queries a store it does not own directly."""

    def __init__(
        self,
        client_store: ClientStorePort,
        document_store: CabinetDocumentStorePort,
        time_entry_store: TimeEntryStorePort,
        ai_usage: AIUsagePort,
    ) -> None:
        self._clients = client_store
        self._documents = document_store
        self._time_entries = time_entry_store
        self._ai_usage = ai_usage

    def compute_firm_analytics(self, firm_id: str) -> FirmAnalytics:
        clients = self._clients.list_for_firm(firm_id)
        entries = self._time_entries.list_for_firm(firm_id)
        billable = sum(e.duration_minutes or 0 for e in entries if e.billable)
        non_billable = sum(e.duration_minutes or 0 for e in entries if not e.billable)
        case_minutes: dict[str, int] = {}
        for entry in entries:
            case_minutes[entry.case_id] = case_minutes.get(entry.case_id, 0) + (
                entry.duration_minutes or 0
            )
        average = sum(case_minutes.values()) / len(case_minutes) if case_minutes else 0.0
        document_count = sum(len(self._documents.list_for_client(c.id)) for c in clients)
        return FirmAnalytics(
            firm_id=firm_id,
            client_count=len(clients),
            active_client_count=sum(1 for c in clients if c.status is ClientStatus.ACTIVE),
            document_count=document_count,
            billable_minutes=billable,
            non_billable_minutes=non_billable,
            ai_requests=self._ai_usage.total_requests(firm_id),
            average_minutes_per_case=average,
            computed_at=datetime.now(UTC),
        )
