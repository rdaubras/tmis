from datetime import UTC, datetime

from tmis.cabinet_os.analytics.ports import AIUsagePort
from tmis.cabinet_os.billing.ports import PaymentStorePort
from tmis.cabinet_os.clients.ports import ClientStorePort
from tmis.cabinet_os.dashboard.schemas import (
    AdminDashboard,
    CabinetDashboard,
    CollaboratorDashboard,
)
from tmis.cabinet_os.deadlines.ports import DeadlineStorePort
from tmis.cabinet_os.deadlines.schemas import DeadlineStatus
from tmis.cabinet_os.hearings.ports import HearingStorePort
from tmis.cabinet_os.subscriptions.ports import SubscriptionEnginePort
from tmis.cabinet_os.time_tracking.ports import TimeEntryStorePort
from tmis.collaboration.tasks.ports import TaskStorePort
from tmis.collaboration.workflow.schemas import WorkflowStatus

_DONE_STATUSES = {WorkflowStatus.VALIDATED, WorkflowStatus.ARCHIVED}


class DashboardEngine:
    """Implements `DashboardEnginePort` (see docs/39-cabinet-os.md —
    Dashboard Engine). Composes the read ports of other engines —
    including `tmis.collaboration.tasks` (Sprint 8) for the
    collaborator view — it never duplicates their storage."""

    def __init__(
        self,
        client_store: ClientStorePort,
        hearing_store: HearingStorePort,
        payment_store: PaymentStorePort,
        time_entry_store: TimeEntryStorePort,
        deadline_store: DeadlineStorePort,
        task_store: TaskStorePort,
        subscription_engine: SubscriptionEnginePort,
        ai_usage: AIUsagePort,
    ) -> None:
        self._clients = client_store
        self._hearings = hearing_store
        self._payments = payment_store
        self._time_entries = time_entry_store
        self._deadlines = deadline_store
        self._tasks = task_store
        self._subscriptions = subscription_engine
        self._ai_usage = ai_usage

    def cabinet_dashboard(self, firm_id: str) -> CabinetDashboard:
        clients = self._clients.list_for_firm(firm_id)
        open_case_count = len({case_id for c in clients for case_id in c.case_ids})
        revenue = sum(p.amount for p in self._payments.list_for_firm(firm_id))
        billable = sum(
            e.duration_minutes or 0
            for e in self._time_entries.list_for_firm(firm_id)
            if e.billable
        )
        return CabinetDashboard(
            firm_id=firm_id,
            revenue=revenue,
            open_case_count=open_case_count,
            hearing_count=len(self._hearings.list_for_firm(firm_id)),
            billable_minutes=billable,
            ai_requests=self._ai_usage.total_requests(firm_id),
            computed_at=datetime.now(UTC),
        )

    def collaborator_dashboard(
        self, firm_id: str, collaborator_id: str
    ) -> CollaboratorDashboard:
        tasks = self._tasks.list_for_assignee(collaborator_id)
        open_tasks = [t for t in tasks if t.status not in _DONE_STATUSES]
        case_ids = {t.case_id for t in tasks if t.case_id is not None}
        upcoming_deadlines = sum(
            1
            for case_id in case_ids
            for d in self._deadlines.list_for_case(case_id)
            if d.status is DeadlineStatus.PENDING
        )
        tracked = sum(
            e.duration_minutes or 0
            for e in self._time_entries.list_for_collaborator(collaborator_id)
        )
        return CollaboratorDashboard(
            collaborator_id=collaborator_id,
            task_count=len(tasks),
            open_task_count=len(open_tasks),
            case_count=len(case_ids),
            upcoming_deadline_count=upcoming_deadlines,
            tracked_minutes=tracked,
            computed_at=datetime.now(UTC),
        )

    def admin_dashboard(self, firm_id: str) -> AdminDashboard:
        subscription = self._subscriptions.get(firm_id)
        usage = self._subscriptions.usage(firm_id)
        return AdminDashboard(
            firm_id=firm_id,
            plan=subscription.plan.value,
            active_users=usage.active_users,
            max_users=subscription.quota.max_users,
            storage_gb_used=usage.storage_gb_used,
            max_storage_gb=subscription.quota.max_storage_gb,
            ai_requests_used=usage.ai_requests_used,
            max_ai_requests_per_month=subscription.quota.max_ai_requests_per_month,
            computed_at=datetime.now(UTC),
        )
