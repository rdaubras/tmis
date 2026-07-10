from fastapi import APIRouter, Depends, HTTPException

from tmis.cabinet_os.api.schemas import (
    AddLineRequest,
    CreateInvoiceRequest,
    InvoiceResponse,
    LogTimeRequest,
    RecordPaymentRequest,
    SubscribeRequest,
    SubscriptionResponse,
    TimeEntryResponse,
)
from tmis.cabinet_os.billing.engine import BillingEngine
from tmis.cabinet_os.billing.schemas import FeeType, Invoice, PaymentMethod
from tmis.cabinet_os.bootstrap import (
    get_billing_engine,
    get_subscription_engine,
    get_time_tracking_service,
)
from tmis.cabinet_os.subscriptions.engine import ConfigurableSubscriptionEngine
from tmis.cabinet_os.subscriptions.schemas import PlanTier
from tmis.cabinet_os.time_tracking.schemas import ActivityType, TimeEntry
from tmis.cabinet_os.time_tracking.service import TimeTrackingService

router = APIRouter(prefix="/cabinet-os", tags=["cabinet-os-billing"])


def _to_invoice_response(invoice: Invoice, total_due: float) -> InvoiceResponse:
    return InvoiceResponse(
        id=invoice.id,
        firm_id=invoice.firm_id,
        client_id=invoice.client_id,
        status=invoice.status.value,
        currency=invoice.currency,
        total_due=total_due,
    )


def _to_time_entry_response(entry: TimeEntry) -> TimeEntryResponse:
    return TimeEntryResponse(
        id=entry.id,
        firm_id=entry.firm_id,
        collaborator_id=entry.collaborator_id,
        case_id=entry.case_id,
        activity_type=entry.activity_type.value,
        entry_method=entry.entry_method.value,
        duration_minutes=entry.duration_minutes,
        billable=entry.billable,
    )


@router.post("/billing/invoices", response_model=InvoiceResponse)
def create_invoice(
    payload: CreateInvoiceRequest, engine: BillingEngine = Depends(get_billing_engine)
) -> InvoiceResponse:
    invoice = engine.create_invoice(payload.firm_id, payload.client_id, payload.case_id)
    return _to_invoice_response(invoice, engine.total_due(invoice.id))


@router.post("/billing/invoices/{invoice_id}/lines", response_model=InvoiceResponse)
def add_invoice_line(
    invoice_id: str,
    payload: AddLineRequest,
    engine: BillingEngine = Depends(get_billing_engine),
) -> InvoiceResponse:
    try:
        fee_type = FeeType(payload.fee_type)
        invoice = engine.add_invoice_line(
            invoice_id,
            payload.description,
            payload.quantity,
            payload.unit_price,
            fee_type=fee_type,
            discount_percent=payload.discount_percent,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_invoice_response(invoice, engine.total_due(invoice.id))


@router.post("/billing/invoices/{invoice_id}/issue", response_model=InvoiceResponse)
def issue_invoice(
    invoice_id: str, engine: BillingEngine = Depends(get_billing_engine)
) -> InvoiceResponse:
    try:
        invoice = engine.issue_invoice(invoice_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_invoice_response(invoice, engine.total_due(invoice.id))


@router.post("/billing/invoices/{invoice_id}/payments", response_model=InvoiceResponse)
def record_payment(
    invoice_id: str,
    payload: RecordPaymentRequest,
    engine: BillingEngine = Depends(get_billing_engine),
) -> InvoiceResponse:
    try:
        method = PaymentMethod(payload.method)
        engine.record_payment(invoice_id, payload.amount, method, payload.reference)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    invoice = engine.get_invoice(invoice_id)
    return _to_invoice_response(invoice, engine.total_due(invoice_id))


@router.get("/billing/invoices/{invoice_id}/total-due")
def get_total_due(
    invoice_id: str, engine: BillingEngine = Depends(get_billing_engine)
) -> dict[str, float]:
    try:
        return {"total_due": engine.total_due(invoice_id)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/time-entries", response_model=TimeEntryResponse)
def log_time(
    payload: LogTimeRequest, service: TimeTrackingService = Depends(get_time_tracking_service)
) -> TimeEntryResponse:
    try:
        activity_type = ActivityType(payload.activity_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"Unknown activity type: {payload.activity_type!r}"
        ) from exc
    entry = service.log(
        payload.firm_id,
        payload.collaborator_id,
        payload.case_id,
        payload.duration_minutes,
        activity_type,
        comments=payload.comments,
        billable=payload.billable,
    )
    return _to_time_entry_response(entry)


@router.post("/subscriptions", response_model=SubscriptionResponse)
def subscribe(
    payload: SubscribeRequest,
    engine: ConfigurableSubscriptionEngine = Depends(get_subscription_engine),
) -> SubscriptionResponse:
    try:
        plan = PlanTier(payload.plan)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {payload.plan!r}") from exc
    subscription = engine.subscribe(payload.firm_id, plan)
    return SubscriptionResponse(
        firm_id=subscription.firm_id,
        plan=subscription.plan.value,
        status=subscription.status.value,
        max_users=subscription.quota.max_users,
        max_ai_requests_per_month=subscription.quota.max_ai_requests_per_month,
        max_storage_gb=subscription.quota.max_storage_gb,
    )


@router.get("/subscriptions/{firm_id}", response_model=SubscriptionResponse)
def get_subscription(
    firm_id: str, engine: ConfigurableSubscriptionEngine = Depends(get_subscription_engine)
) -> SubscriptionResponse:
    try:
        subscription = engine.get(firm_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SubscriptionResponse(
        firm_id=subscription.firm_id,
        plan=subscription.plan.value,
        status=subscription.status.value,
        max_users=subscription.quota.max_users,
        max_ai_requests_per_month=subscription.quota.max_ai_requests_per_month,
        max_storage_gb=subscription.quota.max_storage_gb,
    )
