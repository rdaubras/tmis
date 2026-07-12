from dataclasses import dataclass

from tmis.business_platform.licenses.schemas import LicenseGrant
from tmis.business_platform.modules.schemas import TmisModule
from tmis.business_platform.plans.schemas import Plan
from tmis.business_platform.subscriptions.schemas import Subscription
from tmis.business_platform.tenant_settings.schemas import TenantSettings
from tmis.business_platform.usage.schemas import UsageSnapshot
from tmis.cabinet_os.billing.schemas import Invoice
from tmis.identity_platform.roles.schemas import RoleAssignment
from tmis.identity_platform.users.schemas import User


@dataclass(frozen=True, slots=True)
class CustomerPortalSnapshot:
    """Everything a firm admin sees on the customer portal's landing
    page, aggregated in one read — the eight capabilities the sprint
    asks for (users, licenses, subscription, modules, consumption,
    settings, billing history, quotas via `usage`)."""

    firm_id: str
    users: list[User]
    role_assignments: list[RoleAssignment]
    subscription: Subscription
    plan: Plan
    license_grants: list[LicenseGrant]
    active_modules: list[TmisModule]
    usage: list[UsageSnapshot]
    settings: TenantSettings
    recent_invoices: list[Invoice]
