from dataclasses import dataclass

from tmis.identity_platform.departments.schemas import Department
from tmis.identity_platform.organization.schemas import Organization
from tmis.identity_platform.teams.schemas import Team
from tmis.identity_platform.tenant_context.schemas import TenantProfile
from tmis.identity_platform.users.schemas import User


@dataclass(frozen=True, slots=True)
class TenantHierarchyView:
    """A read-only snapshot of the full hierarchy — "Organisation →
    Départements → Équipes → Utilisateurs → Permissions → Policies →
    Quotas → Branding" (sprint requirement). Permissions and policies
    are resolved separately by `authorization.AuthorizationEngine`,
    referenced by id here rather than embedded."""

    organization: Organization
    tenant_profile: TenantProfile
    departments: tuple[Department, ...]
    teams: tuple[Team, ...]
    users: tuple[User, ...]
