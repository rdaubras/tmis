from pydantic import BaseModel


class OrganizationCreateRequest(BaseModel):
    firm_id: str
    legal_name: str


class OrganizationResponse(BaseModel):
    firm_id: str
    legal_name: str
    status: str


class DepartmentCreateRequest(BaseModel):
    firm_id: str
    name: str


class DepartmentResponse(BaseModel):
    id: str
    firm_id: str
    name: str


class TeamCreateRequest(BaseModel):
    firm_id: str
    department_id: str
    name: str


class TeamResponse(BaseModel):
    id: str
    firm_id: str
    department_id: str
    name: str


class RoleAssignmentRequest(BaseModel):
    firm_id: str
    user_id: str
    role: str


class RoleAssignmentResponse(BaseModel):
    firm_id: str
    user_id: str
    roles: list[str]


class PermissionResponse(BaseModel):
    value: str


class PolicyCreateRequest(BaseModel):
    firm_id: str
    permission: str
    allowed_roles: list[str] = []
    denied_roles: list[str] = []
    restricted_to_team_id: str | None = None
    requires_second_validation: bool = False
    reason: str = ""


class PolicyResponse(BaseModel):
    id: str
    firm_id: str
    permission: str
    allowed_roles: list[str]
    denied_roles: list[str]
    restricted_to_team_id: str | None
    requires_second_validation: bool
    reason: str
    active: bool


class IdentityContextSetRequest(BaseModel):
    firm_id: str
    user_id: str
    specialty: str = ""
    experience_level: str = ""
    seniority_years: int = 0
    team_id: str | None = None
    department_id: str | None = None
    language: str = "fr"
    can_validate: bool = False


class IdentityContextResponse(BaseModel):
    firm_id: str
    user_id: str
    specialty: str
    experience_level: str
    seniority_years: int
    team_id: str | None
    department_id: str | None
    language: str
    can_validate: bool


class AuthorizationCheckRequest(BaseModel):
    firm_id: str
    user_id: str
    permission: str
    confidentiality_level: str = "standard"
    resource_department_id: str | None = None


class AuthorizationCheckResponse(BaseModel):
    allowed: bool
    reason: str
    requires_second_validation: bool


class SessionResponse(BaseModel):
    id: str
    firm_id: str
    user_id: str
    device_id: str | None
    revoked: bool


class DeviceRegisterRequest(BaseModel):
    firm_id: str
    user_id: str
    label: str


class DeviceResponse(BaseModel):
    id: str
    firm_id: str
    user_id: str
    label: str
    trust_level: str


class DelegationCreateRequest(BaseModel):
    firm_id: str
    delegator_id: str
    delegate_id: str
    permissions: list[str]
    ends_at: str


class DelegationResponse(BaseModel):
    id: str
    firm_id: str
    delegator_id: str
    delegate_id: str
    permissions: list[str]
    starts_at: str
    ends_at: str
    revoked: bool


class SecretSetRequest(BaseModel):
    firm_id: str
    key: str
    plaintext: str


class SecretResponse(BaseModel):
    key: str
    firm_id: str
    created_at: str
    rotated_at: str | None


class SecurityEventResponse(BaseModel):
    event_type: str
    firm_id: str
    occurred_at: str
    detail: dict[str, str]


class IdentityDashboardResponse(BaseModel):
    firm_id: str
    active_sessions: int
    mfa_enrolled_users: int
    trusted_devices: int
    active_delegations: int
    active_policies: int
    security_events_total: int
    high_risk_events_last_24h: int
