from tmis.identity_platform.departments.engine import DepartmentEngine
from tmis.identity_platform.departments.store import InMemoryDepartmentStore
from tmis.identity_platform.organization.engine import OrganizationEngine
from tmis.identity_platform.organization.store import InMemoryOrganizationStore
from tmis.identity_platform.teams.engine import TeamEngine
from tmis.identity_platform.teams.store import InMemoryTeamStore
from tmis.identity_platform.tenant_context.engine import TenantContextEngine
from tmis.identity_platform.tenant_context.schemas import TenantBranding, TenantQuota
from tmis.identity_platform.tenant_context.store import InMemoryTenantProfileStore
from tmis.identity_platform.tenant_management.engine import TenantManagementEngine
from tmis.identity_platform.users.engine import UserEngine
from tmis.identity_platform.users.store import InMemoryUserStore


def _components() -> (
    tuple[TenantManagementEngine, OrganizationEngine, DepartmentEngine, TeamEngine, UserEngine]
):
    organizations = OrganizationEngine(InMemoryOrganizationStore())
    departments = DepartmentEngine(InMemoryDepartmentStore())
    teams = TeamEngine(InMemoryTeamStore())
    users = UserEngine(InMemoryUserStore())
    tenant_context = TenantContextEngine(InMemoryTenantProfileStore())
    engine = TenantManagementEngine(organizations, departments, teams, users, tenant_context)
    return engine, organizations, departments, teams, users


def test_onboard_firm_provisions_tenant_profile_and_organization() -> None:
    engine, *_ = _components()

    organization = engine.onboard_firm(
        "firm-1",
        "Cabinet Dupont & Associés",
        quota=TenantQuota(max_users=10),
        branding=TenantBranding(display_name="Cabinet Dupont"),
    )

    assert organization.legal_name == "Cabinet Dupont & Associés"
    assert organization.status.value == "active"


def test_tenant_hierarchy_aggregates_departments_teams_users() -> None:
    engine, _organizations, departments, teams, users = _components()
    engine.onboard_firm("firm-1", "Cabinet A")

    department = departments.create("firm-1", "Corporate")
    teams.create("firm-1", department.id, "M&A")
    users.create("firm-1", "avocat@example.com", "Avocat Un")

    hierarchy = engine.hierarchy("firm-1")

    assert hierarchy.organization.firm_id == "firm-1"
    assert len(hierarchy.departments) == 1
    assert len(hierarchy.teams) == 1
    assert len(hierarchy.users) == 1


def test_hierarchy_raises_for_unprovisioned_firm() -> None:
    engine, *_ = _components()

    try:
        engine.hierarchy("firm-unknown")
        raise AssertionError("expected KeyError")
    except KeyError:
        pass


def test_department_and_team_are_scoped_to_their_firm() -> None:
    departments = DepartmentEngine(InMemoryDepartmentStore())
    teams = TeamEngine(InMemoryTeamStore())

    dept_a = departments.create("firm-a", "Litigation")
    departments.create("firm-b", "Corporate")

    assert [d.id for d in departments.list_for_firm("firm-a")] == [dept_a.id]
    assert len(departments.list_for_firm("firm-b")) == 1

    team = teams.create("firm-a", dept_a.id, "Team A")
    assert teams.list_for_department("firm-a", dept_a.id) == [team]
    assert teams.list_for_department("firm-b", dept_a.id) == []
