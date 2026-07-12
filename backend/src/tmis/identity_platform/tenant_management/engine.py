from tmis.identity_platform.departments.engine import DepartmentEngine
from tmis.identity_platform.organization.engine import OrganizationEngine
from tmis.identity_platform.organization.schemas import Organization
from tmis.identity_platform.teams.engine import TeamEngine
from tmis.identity_platform.tenant_context.engine import TenantContextEngine
from tmis.identity_platform.tenant_context.schemas import TenantBranding, TenantQuota
from tmis.identity_platform.tenant_management.schemas import TenantHierarchyView
from tmis.identity_platform.users.engine import UserEngine


class TenantManagementEngine:
    """Composes `organization`, `departments`, `teams`, `users` and
    `tenant_context` into the single onboarding/hierarchy facade the
    sprint asks for — never reimplements any of the five, only
    orchestrates them. This is the module every other bounded context
    should call to provision a new tenant, not the five sub-engines
    individually."""

    def __init__(
        self,
        organization_engine: OrganizationEngine,
        department_engine: DepartmentEngine,
        team_engine: TeamEngine,
        user_engine: UserEngine,
        tenant_context_engine: TenantContextEngine,
    ) -> None:
        self._organizations = organization_engine
        self._departments = department_engine
        self._teams = team_engine
        self._users = user_engine
        self._tenant_context = tenant_context_engine

    def onboard_firm(
        self,
        firm_id: str,
        legal_name: str,
        quota: TenantQuota | None = None,
        branding: TenantBranding | None = None,
    ) -> Organization:
        self._tenant_context.provision(firm_id, quota=quota, branding=branding)
        return self._organizations.create(firm_id, legal_name)

    def hierarchy(self, firm_id: str) -> TenantHierarchyView:
        organization = self._organizations.get(firm_id)
        tenant_profile = self._tenant_context.get(firm_id)
        if tenant_profile is None:
            raise KeyError(f"tenant profile not provisioned for firm {firm_id!r}")
        departments = tuple(self._departments.list_for_firm(firm_id))
        teams = tuple(
            team
            for department in departments
            for team in self._teams.list_for_department(firm_id, department.id)
        )
        users = tuple(self._users.list_for_firm(firm_id))
        return TenantHierarchyView(
            organization=organization,
            tenant_profile=tenant_profile,
            departments=departments,
            teams=teams,
            users=users,
        )
