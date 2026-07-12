from tmis.business_platform.customer_portal.schemas import CustomerPortalSnapshot
from tmis.business_platform.licenses.engine import LicenseEngine
from tmis.business_platform.modules.engine import ModuleRegistry
from tmis.business_platform.plans.engine import PlanCatalog
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.business_platform.tenant_settings.engine import TenantSettingsEngine
from tmis.business_platform.usage.engine import UsageEngine
from tmis.business_platform.usage.schemas import UsageSnapshot
from tmis.cabinet_os.billing.ports import InvoiceStorePort
from tmis.identity_platform.roles.engine import RoleEngine
from tmis.identity_platform.roles.schemas import RoleAssignment
from tmis.identity_platform.users.engine import UserEngine


class CustomerPortalEngine:
    """Read-mostly aggregator for the customer portal's landing
    page — composes `identity_platform.users`/`roles` (Sprint 19),
    `licenses`, `subscriptions`, `plans`, `modules`, `usage`,
    `tenant_settings`, and `cabinet_os.billing`'s invoice store
    directly, never reimplementing any of their logic. Every field
    on `CustomerPortalSnapshot` is sourced from exactly one owning
    module."""

    def __init__(
        self,
        users: UserEngine,
        roles: RoleEngine,
        subscriptions: SubscriptionEngine,
        plans: PlanCatalog,
        licenses: LicenseEngine,
        modules: ModuleRegistry,
        usage: UsageEngine,
        settings: TenantSettingsEngine,
        invoices: InvoiceStorePort,
    ) -> None:
        self._users = users
        self._roles = roles
        self._subscriptions = subscriptions
        self._plans = plans
        self._licenses = licenses
        self._modules = modules
        self._usage = usage
        self._settings = settings
        self._invoices = invoices

    def snapshot(self, firm_id: str) -> CustomerPortalSnapshot:
        users = self._users.list_for_firm(firm_id)
        role_assignments: list[RoleAssignment] = [
            RoleAssignment(firm_id=firm_id, user_id=user.id, role=role)
            for user in users
            for role in self._roles.roles_for_user(firm_id, user.id)
        ]
        subscription = self._subscriptions.get(firm_id)
        plan = self._plans.get(subscription.plan_id)
        usage_snapshots: list[UsageSnapshot] = self._usage.full_snapshot(firm_id)
        return CustomerPortalSnapshot(
            firm_id=firm_id,
            users=users,
            role_assignments=role_assignments,
            subscription=subscription,
            plan=plan,
            license_grants=self._licenses.active_grants_for_firm(firm_id),
            active_modules=self._modules.active_modules(firm_id),
            usage=usage_snapshots,
            settings=self._settings.get_or_default(firm_id),
            recent_invoices=self._invoices.list_for_firm(firm_id),
        )
