from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.cabinet_os.administration.engine import AdministrationEngine
from tmis.cabinet_os.administration.monitoring import StaticMonitoringAdapter
from tmis.cabinet_os.administration.store import (
    InMemoryConnectorRegistry,
    InMemoryFirmRegistry,
    InMemoryGlobalConfig,
)
from tmis.cabinet_os.analytics.adapters import KernelAIUsageAdapter
from tmis.cabinet_os.analytics.engine import AnalyticsEngine
from tmis.cabinet_os.billing.engine import BillingEngine
from tmis.cabinet_os.billing.gateway import ManualPaymentGateway, NoOpAccountingExport
from tmis.cabinet_os.billing.store import (
    InMemoryCreditNoteStore,
    InMemoryInvoiceStore,
    InMemoryPaymentStore,
    InMemoryQuoteStore,
)
from tmis.cabinet_os.calendar.engine import ConfigurableCalendarEngine
from tmis.cabinet_os.calendar.store import InMemoryCalendarStore
from tmis.cabinet_os.clients.service import ClientService
from tmis.cabinet_os.clients.store import InMemoryClientStore
from tmis.cabinet_os.contacts.service import ContactService
from tmis.cabinet_os.contacts.store import InMemoryContactRelationStore, InMemoryContactStore
from tmis.cabinet_os.crm.engine import CRMEngine
from tmis.cabinet_os.dashboard.engine import DashboardEngine
from tmis.cabinet_os.deadlines.engine import ConfigurableDeadlineEngine
from tmis.cabinet_os.deadlines.store import InMemoryDeadlineStore
from tmis.cabinet_os.documents.service import CabinetDocumentService
from tmis.cabinet_os.documents.store import InMemoryCabinetDocumentStore
from tmis.cabinet_os.hearings.engine import HearingEngine
from tmis.cabinet_os.hearings.store import InMemoryHearingStore
from tmis.cabinet_os.public_api.engine import PublicApiEngine
from tmis.cabinet_os.public_api.rate_limiter import InMemoryRateLimiter
from tmis.cabinet_os.public_api.store import (
    InMemoryApiKeyStore,
    InMemoryOAuthClientStore,
    InMemoryOAuthTokenStore,
)
from tmis.cabinet_os.reports.engine import ReportEngine
from tmis.cabinet_os.settings.engine import SettingsEngine
from tmis.cabinet_os.settings.store import InMemorySettingsStore
from tmis.cabinet_os.subscriptions.engine import ConfigurableSubscriptionEngine
from tmis.cabinet_os.subscriptions.store import InMemorySubscriptionStore, InMemoryUsageStore
from tmis.cabinet_os.time_tracking.service import TimeTrackingService
from tmis.cabinet_os.time_tracking.store import InMemoryTimeEntryStore
from tmis.collaboration.bootstrap import get_task_store


@lru_cache
def get_client_store() -> InMemoryClientStore:
    return InMemoryClientStore()


@lru_cache
def get_client_service() -> ClientService:
    return ClientService(get_client_store())


@lru_cache
def get_contact_store() -> InMemoryContactStore:
    return InMemoryContactStore()


@lru_cache
def get_contact_service() -> ContactService:
    return ContactService(get_contact_store(), InMemoryContactRelationStore())


@lru_cache
def get_crm_engine() -> CRMEngine:
    return CRMEngine(get_client_store(), get_contact_store())


@lru_cache
def get_calendar_store() -> InMemoryCalendarStore:
    return InMemoryCalendarStore()


@lru_cache
def get_calendar_engine() -> ConfigurableCalendarEngine:
    return ConfigurableCalendarEngine(get_calendar_store())


@lru_cache
def get_hearing_store() -> InMemoryHearingStore:
    return InMemoryHearingStore()


@lru_cache
def get_hearing_engine() -> HearingEngine:
    return HearingEngine(get_hearing_store(), get_calendar_engine())


@lru_cache
def get_deadline_store() -> InMemoryDeadlineStore:
    return InMemoryDeadlineStore()


@lru_cache
def get_deadline_engine() -> ConfigurableDeadlineEngine:
    return ConfigurableDeadlineEngine(get_deadline_store())


@lru_cache
def get_time_entry_store() -> InMemoryTimeEntryStore:
    return InMemoryTimeEntryStore()


@lru_cache
def get_time_tracking_service() -> TimeTrackingService:
    return TimeTrackingService(get_time_entry_store())


@lru_cache
def get_quote_store() -> InMemoryQuoteStore:
    return InMemoryQuoteStore()


@lru_cache
def get_invoice_store() -> InMemoryInvoiceStore:
    return InMemoryInvoiceStore()


@lru_cache
def get_payment_store() -> InMemoryPaymentStore:
    return InMemoryPaymentStore()


@lru_cache
def get_billing_engine() -> BillingEngine:
    return BillingEngine(
        get_quote_store(),
        get_invoice_store(),
        InMemoryCreditNoteStore(),
        get_payment_store(),
        ManualPaymentGateway(),
        NoOpAccountingExport(),
    )


@lru_cache
def get_subscription_store() -> InMemorySubscriptionStore:
    return InMemorySubscriptionStore()


@lru_cache
def get_usage_store() -> InMemoryUsageStore:
    return InMemoryUsageStore()


@lru_cache
def get_subscription_engine() -> ConfigurableSubscriptionEngine:
    return ConfigurableSubscriptionEngine(get_subscription_store(), get_usage_store())


@lru_cache
def get_cabinet_document_store() -> InMemoryCabinetDocumentStore:
    return InMemoryCabinetDocumentStore()


@lru_cache
def get_cabinet_document_service() -> CabinetDocumentService:
    return CabinetDocumentService(get_cabinet_document_store())


@lru_cache
def get_ai_usage_adapter() -> KernelAIUsageAdapter:
    return KernelAIUsageAdapter(get_kernel())


@lru_cache
def get_analytics_engine() -> AnalyticsEngine:
    return AnalyticsEngine(
        get_client_store(),
        get_cabinet_document_store(),
        get_time_entry_store(),
        get_ai_usage_adapter(),
    )


@lru_cache
def get_dashboard_engine() -> DashboardEngine:
    return DashboardEngine(
        get_client_store(),
        get_hearing_store(),
        get_payment_store(),
        get_time_entry_store(),
        get_deadline_store(),
        get_task_store(),
        get_subscription_engine(),
        get_ai_usage_adapter(),
    )


@lru_cache
def get_report_engine() -> ReportEngine:
    return ReportEngine()


@lru_cache
def get_settings_engine() -> SettingsEngine:
    return SettingsEngine(InMemorySettingsStore())


@lru_cache
def get_administration_engine() -> AdministrationEngine:
    return AdministrationEngine(
        InMemoryFirmRegistry(),
        InMemoryConnectorRegistry(),
        InMemoryGlobalConfig(),
        StaticMonitoringAdapter(),
    )


@lru_cache
def get_public_api_engine() -> PublicApiEngine:
    return PublicApiEngine(
        InMemoryApiKeyStore(),
        InMemoryOAuthClientStore(),
        InMemoryOAuthTokenStore(),
        InMemoryRateLimiter(),
    )
