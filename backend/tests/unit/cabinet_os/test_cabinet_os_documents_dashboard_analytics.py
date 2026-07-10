from tmis.cabinet_os.analytics.adapters import NullAIUsageAdapter
from tmis.cabinet_os.analytics.engine import AnalyticsEngine
from tmis.cabinet_os.billing.ports import PaymentStorePort
from tmis.cabinet_os.billing.store import InMemoryPaymentStore
from tmis.cabinet_os.clients.schemas import ClientStatus, ClientType
from tmis.cabinet_os.clients.service import ClientService
from tmis.cabinet_os.clients.store import InMemoryClientStore
from tmis.cabinet_os.dashboard.engine import DashboardEngine
from tmis.cabinet_os.deadlines.store import InMemoryDeadlineStore
from tmis.cabinet_os.documents.schemas import DocumentCategory
from tmis.cabinet_os.documents.service import CabinetDocumentService
from tmis.cabinet_os.documents.store import InMemoryCabinetDocumentStore
from tmis.cabinet_os.hearings.store import InMemoryHearingStore
from tmis.cabinet_os.subscriptions.engine import ConfigurableSubscriptionEngine
from tmis.cabinet_os.subscriptions.schemas import PlanTier
from tmis.cabinet_os.subscriptions.store import InMemorySubscriptionStore, InMemoryUsageStore
from tmis.cabinet_os.time_tracking.schemas import ActivityType
from tmis.cabinet_os.time_tracking.service import TimeTrackingService
from tmis.cabinet_os.time_tracking.store import InMemoryTimeEntryStore
from tmis.collaboration.tasks.schemas import Task
from tmis.collaboration.tasks.store import InMemoryTaskStore
from tmis.collaboration.workflow.schemas import WorkflowStatus


def test_register_document_and_list_for_client() -> None:
    service = CabinetDocumentService(InMemoryCabinetDocumentStore())
    document = service.register(
        "firm-1", "client-1", "contrat.pdf", "s3://bucket/contrat.pdf",
        category=DocumentCategory.CONTRACT,
    )

    assert document.category is DocumentCategory.CONTRACT
    assert service.list_for_client("client-1") == [document]


def test_recategorize_document() -> None:
    service = CabinetDocumentService(InMemoryCabinetDocumentStore())
    document = service.register("firm-1", "client-1", "note.pdf", "ref-1")

    updated = service.recategorize(document.id, DocumentCategory.EVIDENCE)

    assert updated.category is DocumentCategory.EVIDENCE


def test_analytics_engine_computes_firm_metrics() -> None:
    client_store = InMemoryClientStore()
    client_service = ClientService(client_store)
    document_store = InMemoryCabinetDocumentStore()
    document_service = CabinetDocumentService(document_store)
    time_store = InMemoryTimeEntryStore()
    time_service = TimeTrackingService(time_store)

    client = client_service.create("firm-1", ClientType.INDIVIDUAL, "Jean Dupont")
    client_service.change_status(client.id, ClientStatus.ACTIVE)
    document_service.register("firm-1", client.id, "f.pdf", "ref-1")
    time_service.log("firm-1", "collab-1", "case-1", 60, ActivityType.RESEARCH)
    time_service.log("firm-1", "collab-1", "case-1", 30, ActivityType.CALL, billable=False)

    engine = AnalyticsEngine(client_store, document_store, time_store, NullAIUsageAdapter())
    analytics = engine.compute_firm_analytics("firm-1")

    assert analytics.client_count == 1
    assert analytics.active_client_count == 1
    assert analytics.document_count == 1
    assert analytics.billable_minutes == 60
    assert analytics.non_billable_minutes == 30
    assert analytics.average_minutes_per_case == 90.0
    assert analytics.ai_requests == 0


def _make_dashboard_engine(
    client_store: InMemoryClientStore,
    hearing_store: InMemoryHearingStore,
    payment_store: PaymentStorePort,
    time_store: InMemoryTimeEntryStore,
    deadline_store: InMemoryDeadlineStore,
    task_store: InMemoryTaskStore,
    subscription_engine: ConfigurableSubscriptionEngine,
) -> DashboardEngine:
    return DashboardEngine(
        client_store,
        hearing_store,
        payment_store,
        time_store,
        deadline_store,
        task_store,
        subscription_engine,
        NullAIUsageAdapter(),
    )


def test_cabinet_dashboard_aggregates_open_cases_and_billable_time() -> None:
    client_store = InMemoryClientStore()
    client_service = ClientService(client_store)
    time_store = InMemoryTimeEntryStore()
    time_service = TimeTrackingService(time_store)
    payment_store = InMemoryPaymentStore()
    subscription_engine = ConfigurableSubscriptionEngine(
        InMemorySubscriptionStore(), InMemoryUsageStore()
    )
    subscription_engine.subscribe("firm-1", PlanTier.SOLO)

    client = client_service.create("firm-1", ClientType.INDIVIDUAL, "Jean Dupont")
    client_service.link_case(client.id, "case-1")
    time_service.log("firm-1", "collab-1", "case-1", 90, ActivityType.RESEARCH)

    engine = _make_dashboard_engine(
        client_store,
        InMemoryHearingStore(),
        payment_store,
        time_store,
        InMemoryDeadlineStore(),
        InMemoryTaskStore(),
        subscription_engine,
    )
    dashboard = engine.cabinet_dashboard("firm-1")

    assert dashboard.open_case_count == 1
    assert dashboard.billable_minutes == 90
    assert dashboard.revenue == 0.0


def test_collaborator_dashboard_uses_collaboration_tasks() -> None:
    task_store = InMemoryTaskStore()
    task_store.save(
        Task(
            id="t1",
            workspace_id="ws-1",
            title="Task 1",
            description="",
            case_id="case-1",
            assignee_id="collab-1",
            status=WorkflowStatus.TODO,
        )
    )
    task_store.save(
        Task(
            id="t2",
            workspace_id="ws-1",
            title="Task 2",
            description="",
            case_id="case-1",
            assignee_id="collab-1",
            status=WorkflowStatus.VALIDATED,
        )
    )
    subscription_engine = ConfigurableSubscriptionEngine(
        InMemorySubscriptionStore(), InMemoryUsageStore()
    )
    subscription_engine.subscribe("firm-1", PlanTier.SOLO)

    engine = _make_dashboard_engine(
        InMemoryClientStore(),
        InMemoryHearingStore(),
        InMemoryPaymentStore(),
        InMemoryTimeEntryStore(),
        InMemoryDeadlineStore(),
        task_store,
        subscription_engine,
    )
    dashboard = engine.collaborator_dashboard("firm-1", "collab-1")

    assert dashboard.task_count == 2
    assert dashboard.open_task_count == 1
    assert dashboard.case_count == 1


def test_admin_dashboard_reflects_subscription_quota_and_usage() -> None:
    subscription_engine = ConfigurableSubscriptionEngine(
        InMemorySubscriptionStore(), InMemoryUsageStore()
    )
    subscription_engine.subscribe("firm-1", PlanTier.CABINET)
    subscription_engine.record_ai_usage("firm-1", 42)
    subscription_engine.set_active_users("firm-1", 3)

    engine = _make_dashboard_engine(
        InMemoryClientStore(),
        InMemoryHearingStore(),
        InMemoryPaymentStore(),
        InMemoryTimeEntryStore(),
        InMemoryDeadlineStore(),
        InMemoryTaskStore(),
        subscription_engine,
    )
    dashboard = engine.admin_dashboard("firm-1")

    assert dashboard.plan == "cabinet"
    assert dashboard.active_users == 3
    assert dashboard.ai_requests_used == 42
    assert dashboard.max_users == 25
