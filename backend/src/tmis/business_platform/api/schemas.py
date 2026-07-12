from pydantic import BaseModel


class PlanResponse(BaseModel):
    id: str
    name: str
    version: int
    max_users: int
    max_storage_gb: float
    max_ai_calls_per_month: int
    features: list[str]
    monthly_price_usd: float
    annual_price_usd: float


class SubscriptionStartTrialRequest(BaseModel):
    firm_id: str
    plan_id: str


class SubscriptionActivateRequest(BaseModel):
    user_id: str
    billing_cycle: str = "monthly"


class SubscriptionChangePlanRequest(BaseModel):
    user_id: str
    plan_id: str


class SubscriptionResponse(BaseModel):
    firm_id: str
    plan_id: str
    status: str
    billing_cycle: str
    trial_ends_at: str | None
    current_period_end: str | None


class LicenseAssignRequest(BaseModel):
    user_id: str
    license_type: str
    holder_id: str
    duration_days: int = 365


class LicenseGrantResponse(BaseModel):
    id: str
    firm_id: str
    license_type: str
    holder_id: str | None
    key: str
    granted_at: str
    expires_at: str
    revoked: bool


class LicenseRevokeRequest(BaseModel):
    user_id: str


class QuotaOverrideRequest(BaseModel):
    user_id: str
    dimension: str
    extra_amount: int


class QuotaLimitResponse(BaseModel):
    firm_id: str
    dimension: str
    limit: int


class FeatureFlagEvaluateRequest(BaseModel):
    firm_id: str | None = None
    user_id: str | None = None
    environment: str = "production"


class FeatureFlagEvaluateResponse(BaseModel):
    key: str
    enabled: bool


class UsageSnapshotResponse(BaseModel):
    dimension: str
    used: float
    limit: int | None
    percent_used: float | None


class ModuleActivationRequest(BaseModel):
    user_id: str


class ModuleStateResponse(BaseModel):
    module: str
    active: bool
    available: bool


class TenantSettingsResponse(BaseModel):
    firm_id: str
    currency: str
    invoicing_language: str
    invoicing_contact_email: str | None
    auto_renew: bool


class TenantSettingsUpdateRequest(BaseModel):
    currency: str | None = None
    invoicing_language: str | None = None
    invoicing_contact_email: str | None = None
    auto_renew: bool | None = None


class BusinessDashboardResponse(BaseModel):
    firm_id: str
    plan_name: str
    monthly_recurring_revenue_usd: float
    total_ai_cost_usd: float
    cache_hit_rate: float
    cache_savings_usd: float
    active_modules_count: int
    usage: list[UsageSnapshotResponse]


class BusinessReportResponse(BaseModel):
    id: str
    firm_id: str
    generated_at: str
    sections: dict[str, str]


class CustomerPortalSnapshotResponse(BaseModel):
    firm_id: str
    user_count: int
    plan_name: str
    subscription_status: str
    active_modules: list[str]
    license_count: int
    usage: list[UsageSnapshotResponse]
    recent_invoice_count: int
