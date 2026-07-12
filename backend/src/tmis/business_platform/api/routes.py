from fastapi import APIRouter, Depends, HTTPException

from tmis.business_platform.analytics.engine import AnalyticsEngine
from tmis.business_platform.api.schemas import (
    BusinessDashboardResponse,
    BusinessReportResponse,
    CustomerPortalSnapshotResponse,
    FeatureFlagEvaluateRequest,
    FeatureFlagEvaluateResponse,
    LicenseAssignRequest,
    LicenseGrantResponse,
    LicenseRevokeRequest,
    ModuleActivationRequest,
    ModuleStateResponse,
    PlanResponse,
    QuotaLimitResponse,
    QuotaOverrideRequest,
    SubscriptionActivateRequest,
    SubscriptionChangePlanRequest,
    SubscriptionResponse,
    SubscriptionStartTrialRequest,
    TenantSettingsResponse,
    TenantSettingsUpdateRequest,
    UsageSnapshotResponse,
)
from tmis.business_platform.bootstrap import (
    get_analytics_engine,
    get_business_feature_flag_engine,
    get_business_quota_engine,
    get_customer_portal_engine,
    get_license_engine,
    get_module_registry,
    get_plan_catalog,
    get_report_engine,
    get_subscription_engine,
    get_tenant_settings_engine,
    get_usage_engine,
)
from tmis.business_platform.customer_portal.engine import CustomerPortalEngine
from tmis.business_platform.feature_flags.engine import BusinessFeatureFlagEngine
from tmis.business_platform.feature_flags.schemas import BusinessFlagContext, Environment
from tmis.business_platform.licenses.engine import LicenseEngine
from tmis.business_platform.licenses.schemas import LicenseGrant, LicenseType
from tmis.business_platform.modules.engine import ModuleNotAvailableError, ModuleRegistry
from tmis.business_platform.modules.schemas import TmisModule
from tmis.business_platform.plans.engine import PlanCatalog
from tmis.business_platform.quotas.engine import BusinessQuotaEngine
from tmis.business_platform.quotas.schemas import QuotaDimension
from tmis.business_platform.reports.engine import ReportEngine
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.business_platform.subscriptions.schemas import BillingCycle, Subscription
from tmis.business_platform.tenant_settings.engine import TenantSettingsEngine
from tmis.business_platform.tenant_settings.schemas import InvoicingLanguage
from tmis.business_platform.usage.engine import UsageEngine
from tmis.identity_platform.api.guard import authorize_or_403
from tmis.identity_platform.permissions.schemas import Permission

router = APIRouter(prefix="/business-platform", tags=["business-platform"])


def _subscription_response(subscription: Subscription) -> SubscriptionResponse:
    return SubscriptionResponse(
        firm_id=subscription.firm_id,
        plan_id=subscription.plan_id,
        status=subscription.status.value,
        billing_cycle=subscription.billing_cycle.value,
        trial_ends_at=(
            subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None
        ),
        current_period_end=(
            subscription.current_period_end.isoformat() if subscription.current_period_end else None
        ),
    )


def _license_response(grant: LicenseGrant) -> LicenseGrantResponse:
    return LicenseGrantResponse(
        id=grant.id,
        firm_id=grant.firm_id,
        license_type=grant.license_type.value,
        holder_id=grant.holder_id,
        key=grant.key,
        granted_at=grant.granted_at.isoformat(),
        expires_at=grant.expires_at.isoformat(),
        revoked=grant.revoked,
    )


@router.get("/plans", response_model=list[PlanResponse])
def list_plans(catalog: PlanCatalog = Depends(get_plan_catalog)) -> list[PlanResponse]:
    return [
        PlanResponse(
            id=plan.id,
            name=plan.name.value,
            version=plan.version,
            max_users=plan.limits.max_users,
            max_storage_gb=plan.limits.max_storage_gb,
            max_ai_calls_per_month=plan.limits.max_ai_calls_per_month,
            features=sorted(plan.features),
            monthly_price_usd=plan.monthly_price_usd,
            annual_price_usd=plan.annual_price_usd,
        )
        for plan in catalog.list_current_catalog()
    ]


@router.post("/subscriptions/trial", response_model=SubscriptionResponse)
def start_trial(
    payload: SubscriptionStartTrialRequest,
    subscriptions: SubscriptionEngine = Depends(get_subscription_engine),
) -> SubscriptionResponse:
    try:
        subscription = subscriptions.start_trial(payload.firm_id, payload.plan_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _subscription_response(subscription)


@router.post("/subscriptions/{firm_id}/activate", response_model=SubscriptionResponse)
def activate_subscription(
    firm_id: str,
    payload: SubscriptionActivateRequest,
    subscriptions: SubscriptionEngine = Depends(get_subscription_engine),
) -> SubscriptionResponse:
    authorize_or_403(firm_id, payload.user_id, Permission.BUSINESS_PLATFORM_MANAGE)
    try:
        subscription = subscriptions.activate(firm_id, BillingCycle(payload.billing_cycle))
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _subscription_response(subscription)


@router.post("/subscriptions/{firm_id}/change-plan", response_model=SubscriptionResponse)
def change_plan(
    firm_id: str,
    payload: SubscriptionChangePlanRequest,
    subscriptions: SubscriptionEngine = Depends(get_subscription_engine),
) -> SubscriptionResponse:
    authorize_or_403(firm_id, payload.user_id, Permission.BUSINESS_PLATFORM_MANAGE)
    try:
        subscription = subscriptions.change_plan(firm_id, payload.plan_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _subscription_response(subscription)


@router.get("/subscriptions/{firm_id}", response_model=SubscriptionResponse)
def get_subscription(
    firm_id: str, subscriptions: SubscriptionEngine = Depends(get_subscription_engine)
) -> SubscriptionResponse:
    try:
        subscription = subscriptions.get(firm_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _subscription_response(subscription)


@router.post("/licenses/{firm_id}/assign", response_model=LicenseGrantResponse)
def assign_license(
    firm_id: str,
    payload: LicenseAssignRequest,
    licenses: LicenseEngine = Depends(get_license_engine),
) -> LicenseGrantResponse:
    authorize_or_403(firm_id, payload.user_id, Permission.BUSINESS_PLATFORM_MANAGE)
    try:
        license_type = LicenseType(payload.license_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    grant = licenses.assign(
        firm_id, license_type, payload.holder_id, duration_days=payload.duration_days
    )
    return _license_response(grant)


@router.post("/licenses/{firm_id}/{grant_id}/revoke", response_model=LicenseGrantResponse)
def revoke_license(
    firm_id: str,
    grant_id: str,
    payload: LicenseRevokeRequest,
    licenses: LicenseEngine = Depends(get_license_engine),
) -> LicenseGrantResponse:
    authorize_or_403(firm_id, payload.user_id, Permission.BUSINESS_PLATFORM_MANAGE)
    try:
        grant = licenses.revoke(firm_id, grant_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _license_response(grant)


@router.get("/licenses/{firm_id}", response_model=list[LicenseGrantResponse])
def list_licenses(
    firm_id: str, licenses: LicenseEngine = Depends(get_license_engine)
) -> list[LicenseGrantResponse]:
    return [_license_response(grant) for grant in licenses.active_grants_for_firm(firm_id)]


@router.get("/quotas/{firm_id}/{dimension}", response_model=QuotaLimitResponse)
def get_quota_limit(
    firm_id: str, dimension: str, quotas: BusinessQuotaEngine = Depends(get_business_quota_engine)
) -> QuotaLimitResponse:
    try:
        quota_dimension = QuotaDimension(dimension)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    limit = quotas.limit_for(firm_id, quota_dimension)
    return QuotaLimitResponse(firm_id=firm_id, dimension=quota_dimension.value, limit=limit)


@router.post("/quotas/{firm_id}/override", response_model=QuotaLimitResponse)
def set_quota_override(
    firm_id: str,
    payload: QuotaOverrideRequest,
    quotas: BusinessQuotaEngine = Depends(get_business_quota_engine),
) -> QuotaLimitResponse:
    authorize_or_403(firm_id, payload.user_id, Permission.BUSINESS_PLATFORM_MANAGE)
    try:
        quota_dimension = QuotaDimension(payload.dimension)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    quotas.set_override(firm_id, quota_dimension, payload.extra_amount)
    limit = quotas.limit_for(firm_id, quota_dimension)
    return QuotaLimitResponse(firm_id=firm_id, dimension=quota_dimension.value, limit=limit)


@router.post("/feature-flags/{key}/evaluate", response_model=FeatureFlagEvaluateResponse)
def evaluate_feature_flag(
    key: str,
    payload: FeatureFlagEvaluateRequest,
    flags: BusinessFeatureFlagEngine = Depends(get_business_feature_flag_engine),
) -> FeatureFlagEvaluateResponse:
    try:
        environment = Environment(payload.environment)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    context = BusinessFlagContext(
        firm_id=payload.firm_id, user_id=payload.user_id, environment=environment
    )
    return FeatureFlagEvaluateResponse(key=key, enabled=flags.is_enabled(key, context))


@router.get("/usage/{firm_id}", response_model=list[UsageSnapshotResponse])
def get_usage(
    firm_id: str, usage: UsageEngine = Depends(get_usage_engine)
) -> list[UsageSnapshotResponse]:
    return [
        UsageSnapshotResponse(
            dimension=snapshot.dimension.value,
            used=snapshot.used,
            limit=snapshot.limit,
            percent_used=snapshot.percent_used,
        )
        for snapshot in usage.full_snapshot(firm_id)
    ]


@router.get("/modules/{firm_id}", response_model=list[ModuleStateResponse])
def list_modules(
    firm_id: str, modules: ModuleRegistry = Depends(get_module_registry)
) -> list[ModuleStateResponse]:
    return [
        ModuleStateResponse(
            module=module.value,
            active=modules.is_active(firm_id, module),
            available=modules.is_available(firm_id, module),
        )
        for module in TmisModule
    ]


@router.post("/modules/{firm_id}/{module}/activate", response_model=ModuleStateResponse)
def activate_module(
    firm_id: str,
    module: str,
    payload: ModuleActivationRequest,
    modules: ModuleRegistry = Depends(get_module_registry),
) -> ModuleStateResponse:
    authorize_or_403(firm_id, payload.user_id, Permission.BUSINESS_PLATFORM_MANAGE)
    try:
        tmis_module = TmisModule(module)
        modules.activate(firm_id, tmis_module)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ModuleNotAvailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ModuleStateResponse(
        module=tmis_module.value,
        active=modules.is_active(firm_id, tmis_module),
        available=modules.is_available(firm_id, tmis_module),
    )


@router.post("/modules/{firm_id}/{module}/deactivate", response_model=ModuleStateResponse)
def deactivate_module(
    firm_id: str,
    module: str,
    payload: ModuleActivationRequest,
    modules: ModuleRegistry = Depends(get_module_registry),
) -> ModuleStateResponse:
    authorize_or_403(firm_id, payload.user_id, Permission.BUSINESS_PLATFORM_MANAGE)
    try:
        tmis_module = TmisModule(module)
        modules.deactivate(firm_id, tmis_module)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ModuleStateResponse(
        module=tmis_module.value,
        active=modules.is_active(firm_id, tmis_module),
        available=modules.is_available(firm_id, tmis_module),
    )


@router.get("/tenant-settings/{firm_id}", response_model=TenantSettingsResponse)
def get_tenant_settings(
    firm_id: str, settings: TenantSettingsEngine = Depends(get_tenant_settings_engine)
) -> TenantSettingsResponse:
    tenant_settings = settings.get_or_default(firm_id)
    return TenantSettingsResponse(
        firm_id=tenant_settings.firm_id,
        currency=tenant_settings.currency,
        invoicing_language=tenant_settings.invoicing_language.value,
        invoicing_contact_email=tenant_settings.invoicing_contact_email,
        auto_renew=tenant_settings.auto_renew,
    )


@router.put("/tenant-settings/{firm_id}", response_model=TenantSettingsResponse)
def update_tenant_settings(
    firm_id: str,
    payload: TenantSettingsUpdateRequest,
    settings: TenantSettingsEngine = Depends(get_tenant_settings_engine),
) -> TenantSettingsResponse:
    tenant_settings = settings.update(
        firm_id,
        currency=payload.currency,
        invoicing_language=(
            InvoicingLanguage(payload.invoicing_language) if payload.invoicing_language else None
        ),
        invoicing_contact_email=payload.invoicing_contact_email,
        auto_renew=payload.auto_renew,
    )
    return TenantSettingsResponse(
        firm_id=tenant_settings.firm_id,
        currency=tenant_settings.currency,
        invoicing_language=tenant_settings.invoicing_language.value,
        invoicing_contact_email=tenant_settings.invoicing_contact_email,
        auto_renew=tenant_settings.auto_renew,
    )


@router.get("/analytics/{firm_id}", response_model=BusinessDashboardResponse)
def get_analytics(
    firm_id: str, analytics: AnalyticsEngine = Depends(get_analytics_engine)
) -> BusinessDashboardResponse:
    try:
        dashboard = analytics.build_dashboard(firm_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return BusinessDashboardResponse(
        firm_id=dashboard.firm_id,
        plan_name=dashboard.plan_name.value,
        monthly_recurring_revenue_usd=dashboard.monthly_recurring_revenue_usd,
        total_ai_cost_usd=dashboard.total_ai_cost_usd,
        cache_hit_rate=dashboard.cache_hit_rate,
        cache_savings_usd=dashboard.cache_savings_usd,
        active_modules_count=dashboard.active_modules_count,
        usage=[
            UsageSnapshotResponse(
                dimension=snapshot.dimension.value,
                used=snapshot.used,
                limit=snapshot.limit,
                percent_used=snapshot.percent_used,
            )
            for snapshot in dashboard.usage
        ],
    )


@router.post("/reports/{firm_id}/generate", response_model=BusinessReportResponse)
def generate_report(
    firm_id: str, reports: ReportEngine = Depends(get_report_engine)
) -> BusinessReportResponse:
    try:
        report = reports.generate(firm_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return BusinessReportResponse(
        id=report.id,
        firm_id=report.firm_id,
        generated_at=report.generated_at.isoformat(),
        sections=report.sections,
    )


@router.get("/customer-portal/{firm_id}", response_model=CustomerPortalSnapshotResponse)
def get_customer_portal_snapshot(
    firm_id: str, portal: CustomerPortalEngine = Depends(get_customer_portal_engine)
) -> CustomerPortalSnapshotResponse:
    try:
        snapshot = portal.snapshot(firm_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CustomerPortalSnapshotResponse(
        firm_id=snapshot.firm_id,
        user_count=len(snapshot.users),
        plan_name=snapshot.plan.name.value,
        subscription_status=snapshot.subscription.status.value,
        active_modules=[module.value for module in snapshot.active_modules],
        license_count=len(snapshot.license_grants),
        usage=[
            UsageSnapshotResponse(
                dimension=s.dimension.value, used=s.used, limit=s.limit, percent_used=s.percent_used
            )
            for s in snapshot.usage
        ],
        recent_invoice_count=len(snapshot.recent_invoices),
    )
