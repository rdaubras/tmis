from datetime import datetime

from pydantic import BaseModel


# --- CRM / Clients / Contacts -----------------------------------------
class CreateClientRequest(BaseModel):
    firm_id: str
    client_type: str
    display_name: str
    email: str = ""
    phone: str = ""
    first_name: str = ""
    last_name: str = ""
    legal_form: str = ""
    registration_number: str = ""


class ClientResponse(BaseModel):
    id: str
    firm_id: str
    client_type: str
    display_name: str
    email: str
    phone: str
    status: str
    case_ids: list[str]
    document_ids: list[str]
    contact_ids: list[str]


class AddClientNoteRequest(BaseModel):
    author_id: str
    text: str


class ChangeClientStatusRequest(BaseModel):
    target: str
    actor_id: str | None = None


class CreateContactRequest(BaseModel):
    firm_id: str
    role: str
    display_name: str
    email: str = ""
    phone: str = ""
    organization_client_id: str | None = None


class ContactResponse(BaseModel):
    id: str
    firm_id: str
    role: str
    display_name: str
    email: str
    phone: str


# --- Calendar / Hearings / Deadlines -----------------------------------
class ScheduleEventRequest(BaseModel):
    firm_id: str
    event_type: str
    title: str
    starts_at: datetime
    ends_at: datetime | None = None
    case_id: str | None = None
    location: str = ""


class CalendarEventResponse(BaseModel):
    id: str
    firm_id: str
    event_type: str
    title: str
    starts_at: datetime
    ends_at: datetime | None
    location: str


class ScheduleHearingRequest(BaseModel):
    firm_id: str
    case_id: str
    jurisdiction: str
    chamber: str
    scheduled_at: datetime
    room: str = ""


class HearingResponse(BaseModel):
    id: str
    firm_id: str
    case_id: str
    jurisdiction: str
    chamber: str
    scheduled_at: datetime
    room: str
    decision: str | None
    calendar_event_id: str | None
    reminder_event_id: str | None


class RecordHearingDecisionRequest(BaseModel):
    decision: str


class CreateDeadlineRequest(BaseModel):
    firm_id: str
    case_id: str
    label: str
    due_at: datetime


class DeadlineResponse(BaseModel):
    id: str
    firm_id: str
    case_id: str
    label: str
    due_at: datetime
    status: str


# --- Time tracking -------------------------------------------------
class LogTimeRequest(BaseModel):
    firm_id: str
    collaborator_id: str
    case_id: str
    duration_minutes: int
    activity_type: str
    comments: str = ""
    billable: bool = True


class TimeEntryResponse(BaseModel):
    id: str
    firm_id: str
    collaborator_id: str
    case_id: str
    activity_type: str
    entry_method: str
    duration_minutes: int | None
    billable: bool


# --- Billing --------------------------------------------------------
class CreateInvoiceRequest(BaseModel):
    firm_id: str
    client_id: str
    case_id: str | None = None


class AddLineRequest(BaseModel):
    description: str
    quantity: float
    unit_price: float
    fee_type: str = "hourly"
    discount_percent: float = 0.0


class InvoiceResponse(BaseModel):
    id: str
    firm_id: str
    client_id: str
    status: str
    currency: str
    total_due: float


class RecordPaymentRequest(BaseModel):
    amount: float
    method: str
    reference: str = ""


# --- Subscriptions ----------------------------------------------------
class SubscribeRequest(BaseModel):
    firm_id: str
    plan: str


class SubscriptionResponse(BaseModel):
    firm_id: str
    plan: str
    status: str
    max_users: int
    max_ai_requests_per_month: int
    max_storage_gb: float


# --- Documents --------------------------------------------------------
class RegisterDocumentRequest(BaseModel):
    firm_id: str
    client_id: str
    filename: str
    storage_ref: str
    category: str = "other"
    case_id: str | None = None


class CabinetDocumentResponse(BaseModel):
    id: str
    firm_id: str
    client_id: str
    filename: str
    category: str
    case_id: str | None


# --- Dashboards / Analytics --------------------------------------------
class CabinetDashboardResponse(BaseModel):
    firm_id: str
    revenue: float
    open_case_count: int
    hearing_count: int
    billable_minutes: int
    ai_requests: int


class CollaboratorDashboardResponse(BaseModel):
    collaborator_id: str
    task_count: int
    open_task_count: int
    case_count: int
    upcoming_deadline_count: int
    tracked_minutes: int


class AdminDashboardResponse(BaseModel):
    firm_id: str
    plan: str
    active_users: int
    max_users: int
    storage_gb_used: float
    max_storage_gb: float
    ai_requests_used: int
    max_ai_requests_per_month: int


class FirmAnalyticsResponse(BaseModel):
    firm_id: str
    client_count: int
    active_client_count: int
    document_count: int
    billable_minutes: int
    non_billable_minutes: int
    ai_requests: int
    average_minutes_per_case: float


# --- Reports -----------------------------------------------------------
class GenerateReportRequest(BaseModel):
    title: str
    headers: list[str]
    rows: list[list[str]]
    report_format: str


# --- Settings -----------------------------------------------------------
class SetSettingRequest(BaseModel):
    value: str


class SettingResponse(BaseModel):
    firm_id: str
    category: str
    key: str
    value: str


# --- Administration ------------------------------------------------------
class RegisterFirmRequest(BaseModel):
    name: str


class FirmRecordResponse(BaseModel):
    id: str
    name: str
    status: str


class SetFirmStatusRequest(BaseModel):
    status: str


class RegisterConnectorRequest(BaseModel):
    name: str
    connector_type: str


class ConnectorStatusResponse(BaseModel):
    name: str
    connector_type: str
    enabled: bool


class SetGlobalConfigRequest(BaseModel):
    key: str
    value: str


class MonitoringSnapshotResponse(BaseModel):
    cpu_percent: float
    memory_percent: float
    request_latency_ms_p50: float
    request_latency_ms_p95: float
    error_rate: float


# --- Public API -----------------------------------------------------------
class IssueApiKeyRequest(BaseModel):
    firm_id: str
    name: str
    scopes: list[str]


class ApiKeyResponse(BaseModel):
    id: str
    firm_id: str
    name: str
    prefix: str
    scopes: list[str]
    raw_key: str | None = None


class RegisterOAuthClientRequest(BaseModel):
    firm_id: str
    redirect_uris: list[str]
    scopes: list[str]


class OAuthClientResponse(BaseModel):
    client_id: str
    client_secret: str | None = None
    scopes: list[str]


class IssueOAuthTokenRequest(BaseModel):
    client_id: str
    client_secret: str


class OAuthTokenResponse(BaseModel):
    token: str
    expires_at: datetime
    scopes: list[str]
