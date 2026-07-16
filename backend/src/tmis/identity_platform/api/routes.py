import dataclasses
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from tmis.api.deps import Principal, require_role
from tmis.identity_platform.abac.schemas import AbacAttributes
from tmis.identity_platform.api.schemas import (
    AuthorizationCheckRequest,
    AuthorizationCheckResponse,
    DelegationCreateRequest,
    DelegationResponse,
    DepartmentCreateRequest,
    DepartmentResponse,
    DeviceRegisterRequest,
    DeviceResponse,
    IdentityContextResponse,
    IdentityContextSetRequest,
    IdentityDashboardResponse,
    OrganizationCreateRequest,
    OrganizationResponse,
    PermissionResponse,
    PolicyCreateRequest,
    PolicyResponse,
    RoleAssignmentRequest,
    RoleAssignmentResponse,
    SecretResponse,
    SecretSetRequest,
    SecurityEventResponse,
    SessionResponse,
    TeamCreateRequest,
    TeamResponse,
)
from tmis.identity_platform.authorization.engine import AuthorizationEngine
from tmis.identity_platform.bootstrap import (
    get_authorization_engine,
    get_delegation_engine,
    get_department_engine,
    get_device_trust_engine,
    get_identity_context_engine,
    get_identity_monitoring_engine,
    get_organization_engine,
    get_policy_engine,
    get_role_engine,
    get_secret_manager_engine,
    get_security_event_bus,
    get_session_manager,
    get_team_engine,
)
from tmis.identity_platform.delegation.engine import DelegationEngine
from tmis.identity_platform.delegation.schemas import Delegation
from tmis.identity_platform.departments.engine import DepartmentEngine
from tmis.identity_platform.departments.schemas import Department
from tmis.identity_platform.device_trust.engine import DeviceTrustEngine
from tmis.identity_platform.device_trust.schemas import Device
from tmis.identity_platform.identity_context.engine import IdentityContextEngine
from tmis.identity_platform.identity_context.schemas import IdentityContext
from tmis.identity_platform.monitoring.engine import IdentityMonitoringEngine
from tmis.identity_platform.organization.engine import OrganizationEngine
from tmis.identity_platform.permissions.schemas import Permission
from tmis.identity_platform.policy_engine.engine import PolicyEngine
from tmis.identity_platform.policy_engine.schemas import Policy
from tmis.identity_platform.roles.engine import RoleEngine
from tmis.identity_platform.roles.schemas import Role
from tmis.identity_platform.secret_manager.engine import SecretManagerEngine
from tmis.identity_platform.secret_manager.schemas import ManagedSecret
from tmis.identity_platform.security_events.bus import SecurityEventBus
from tmis.identity_platform.security_events.schemas import SecurityEvent
from tmis.identity_platform.session_manager.engine import SessionManager
from tmis.identity_platform.session_manager.schemas import Session
from tmis.identity_platform.teams.engine import TeamEngine
from tmis.identity_platform.teams.schemas import Team

router = APIRouter(prefix="/identity-platform", tags=["identity-platform"])

_EVENT_COMMON_FIELDS = frozenset({"firm_id", "event_id", "occurred_at"})


@router.post("/organizations", response_model=OrganizationResponse)
def create_organization(
    payload: OrganizationCreateRequest,
    organizations: OrganizationEngine = Depends(get_organization_engine),
) -> OrganizationResponse:
    organization = organizations.create(payload.firm_id, payload.legal_name)
    return OrganizationResponse(
        firm_id=organization.firm_id,
        legal_name=organization.legal_name,
        status=organization.status.value,
    )


@router.get("/organizations/{firm_id}", response_model=OrganizationResponse)
def get_organization(
    firm_id: str, organizations: OrganizationEngine = Depends(get_organization_engine)
) -> OrganizationResponse:
    try:
        organization = organizations.get(firm_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OrganizationResponse(
        firm_id=organization.firm_id,
        legal_name=organization.legal_name,
        status=organization.status.value,
    )


def _department_response(department: Department) -> DepartmentResponse:
    return DepartmentResponse(id=department.id, firm_id=department.firm_id, name=department.name)


@router.post("/departments", response_model=DepartmentResponse)
def create_department(
    payload: DepartmentCreateRequest,
    departments: DepartmentEngine = Depends(get_department_engine),
) -> DepartmentResponse:
    return _department_response(departments.create(payload.firm_id, payload.name))


@router.get("/departments", response_model=list[DepartmentResponse])
def list_departments(
    firm_id: str, departments: DepartmentEngine = Depends(get_department_engine)
) -> list[DepartmentResponse]:
    return [_department_response(d) for d in departments.list_for_firm(firm_id)]


def _team_response(team: Team) -> TeamResponse:
    return TeamResponse(
        id=team.id, firm_id=team.firm_id, department_id=team.department_id, name=team.name
    )


@router.post("/teams", response_model=TeamResponse)
def create_team(
    payload: TeamCreateRequest, teams: TeamEngine = Depends(get_team_engine)
) -> TeamResponse:
    return _team_response(teams.create(payload.firm_id, payload.department_id, payload.name))


@router.get("/teams", response_model=list[TeamResponse])
def list_teams(
    firm_id: str,
    department_id: str,
    teams: TeamEngine = Depends(get_team_engine),
) -> list[TeamResponse]:
    return [_team_response(t) for t in teams.list_for_department(firm_id, department_id)]


@router.post("/roles", response_model=RoleAssignmentResponse)
def assign_role(
    payload: RoleAssignmentRequest, roles: RoleEngine = Depends(get_role_engine)
) -> RoleAssignmentResponse:
    try:
        role = Role(payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    roles.assign(payload.firm_id, payload.user_id, role)
    return RoleAssignmentResponse(
        firm_id=payload.firm_id,
        user_id=payload.user_id,
        roles=[r.value for r in roles.roles_for_user(payload.firm_id, payload.user_id)],
    )


@router.get("/roles", response_model=RoleAssignmentResponse)
def get_roles(
    firm_id: str, user_id: str, roles: RoleEngine = Depends(get_role_engine)
) -> RoleAssignmentResponse:
    return RoleAssignmentResponse(
        firm_id=firm_id,
        user_id=user_id,
        roles=[r.value for r in roles.roles_for_user(firm_id, user_id)],
    )


@router.get("/permissions", response_model=list[PermissionResponse])
def list_permissions() -> list[PermissionResponse]:
    return [PermissionResponse(value=p.value) for p in Permission]


def _identity_context_response(context: IdentityContext) -> IdentityContextResponse:
    return IdentityContextResponse(
        firm_id=context.firm_id,
        user_id=context.user_id,
        specialty=context.specialty,
        experience_level=context.experience_level,
        seniority_years=context.seniority_years,
        team_id=context.team_id,
        department_id=context.department_id,
        language=context.language,
        can_validate=context.can_validate,
    )


@router.put("/identity-context", response_model=IdentityContextResponse)
def set_identity_context(
    payload: IdentityContextSetRequest,
    identity_context: IdentityContextEngine = Depends(get_identity_context_engine),
) -> IdentityContextResponse:
    context = identity_context.set_context(
        IdentityContext(
            user_id=payload.user_id,
            firm_id=payload.firm_id,
            specialty=payload.specialty,
            experience_level=payload.experience_level,
            seniority_years=payload.seniority_years,
            team_id=payload.team_id,
            department_id=payload.department_id,
            language=payload.language,
            can_validate=payload.can_validate,
        )
    )
    return _identity_context_response(context)


@router.get("/identity-context", response_model=IdentityContextResponse)
def get_identity_context(
    firm_id: str,
    user_id: str,
    identity_context: IdentityContextEngine = Depends(get_identity_context_engine),
) -> IdentityContextResponse:
    return _identity_context_response(identity_context.get_or_default(firm_id, user_id))


def _policy_response(policy: Policy) -> PolicyResponse:
    return PolicyResponse(
        id=policy.id,
        firm_id=policy.firm_id,
        permission=policy.permission.value,
        allowed_roles=[r.value for r in policy.allowed_roles],
        denied_roles=[r.value for r in policy.denied_roles],
        restricted_to_team_id=policy.restricted_to_team_id,
        requires_second_validation=policy.requires_second_validation,
        reason=policy.reason,
        active=policy.active,
    )


@router.post("/policies", response_model=PolicyResponse)
def create_policy(
    payload: PolicyCreateRequest, policies: PolicyEngine = Depends(get_policy_engine)
) -> PolicyResponse:
    try:
        permission = Permission(payload.permission)
        allowed_roles = frozenset(Role(r) for r in payload.allowed_roles)
        denied_roles = frozenset(Role(r) for r in payload.denied_roles)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    policy = policies.create(
        payload.firm_id,
        permission,
        allowed_roles=allowed_roles,
        denied_roles=denied_roles,
        restricted_to_team_id=payload.restricted_to_team_id,
        requires_second_validation=payload.requires_second_validation,
        reason=payload.reason,
    )
    return _policy_response(policy)


@router.get("/policies", response_model=list[PolicyResponse])
def list_policies(
    firm_id: str, policies: PolicyEngine = Depends(get_policy_engine)
) -> list[PolicyResponse]:
    return [_policy_response(p) for p in policies.list_active_for_firm(firm_id)]


@router.post("/authorize", response_model=AuthorizationCheckResponse)
def check_authorization(
    payload: AuthorizationCheckRequest,
    authorization: AuthorizationEngine = Depends(get_authorization_engine),
    identity_context: IdentityContextEngine = Depends(get_identity_context_engine),
) -> AuthorizationCheckResponse:
    try:
        permission = Permission(payload.permission)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    identity = identity_context.get_or_default(payload.firm_id, payload.user_id)
    attributes = AbacAttributes(
        confidentiality_level=payload.confidentiality_level,
        department_id=payload.resource_department_id,
    )
    decision = authorization.check(identity, permission, attributes)
    return AuthorizationCheckResponse(
        allowed=decision.allowed,
        reason=decision.reason,
        requires_second_validation=decision.requires_second_validation,
    )


def _session_response(session: Session) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        firm_id=session.firm_id,
        user_id=session.user_id,
        device_id=session.device_id,
        revoked=session.revoked,
    )


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    firm_id: str, user_id: str, sessions: SessionManager = Depends(get_session_manager)
) -> list[SessionResponse]:
    return [_session_response(s) for s in sessions.list_for_user(firm_id, user_id)]


@router.post("/sessions/{session_id}/revoke", response_model=SessionResponse)
def revoke_session(
    session_id: str, firm_id: str, sessions: SessionManager = Depends(get_session_manager)
) -> SessionResponse:
    try:
        session = sessions.revoke(firm_id, session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _session_response(session)


def _device_response(device: Device) -> DeviceResponse:
    return DeviceResponse(
        id=device.id,
        firm_id=device.firm_id,
        user_id=device.user_id,
        label=device.label,
        trust_level=device.trust_level.value,
    )


@router.post("/devices", response_model=DeviceResponse)
def register_device(
    payload: DeviceRegisterRequest, devices: DeviceTrustEngine = Depends(get_device_trust_engine)
) -> DeviceResponse:
    return _device_response(devices.register(payload.firm_id, payload.user_id, payload.label))


@router.get("/devices", response_model=list[DeviceResponse])
def list_devices(
    firm_id: str, user_id: str, devices: DeviceTrustEngine = Depends(get_device_trust_engine)
) -> list[DeviceResponse]:
    return [_device_response(d) for d in devices.list_for_user(firm_id, user_id)]


@router.post("/devices/{device_id}/trust", response_model=DeviceResponse)
def trust_device(
    device_id: str, firm_id: str, devices: DeviceTrustEngine = Depends(get_device_trust_engine)
) -> DeviceResponse:
    try:
        device = devices.trust(firm_id, device_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _device_response(device)


@router.post("/devices/{device_id}/revoke", response_model=DeviceResponse)
def revoke_device(
    device_id: str, firm_id: str, devices: DeviceTrustEngine = Depends(get_device_trust_engine)
) -> DeviceResponse:
    try:
        device = devices.revoke(firm_id, device_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _device_response(device)


def _delegation_response(delegation: Delegation) -> DelegationResponse:
    return DelegationResponse(
        id=delegation.id,
        firm_id=delegation.firm_id,
        delegator_id=delegation.delegator_id,
        delegate_id=delegation.delegate_id,
        permissions=[p.value for p in delegation.permissions],
        starts_at=delegation.starts_at.isoformat(),
        ends_at=delegation.ends_at.isoformat(),
        revoked=delegation.revoked,
    )


@router.post("/delegations", response_model=DelegationResponse)
def create_delegation(
    payload: DelegationCreateRequest, delegations: DelegationEngine = Depends(get_delegation_engine)
) -> DelegationResponse:
    try:
        permissions = frozenset(Permission(p) for p in payload.permissions)
        ends_at = datetime.fromisoformat(payload.ends_at)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    delegation = delegations.grant(
        payload.firm_id, payload.delegator_id, payload.delegate_id, permissions, ends_at
    )
    return _delegation_response(delegation)


@router.get("/delegations", response_model=list[DelegationResponse])
def list_delegations(
    firm_id: str, delegations: DelegationEngine = Depends(get_delegation_engine)
) -> list[DelegationResponse]:
    return [_delegation_response(d) for d in delegations.active_delegations_for_firm(firm_id)]


@router.post("/delegations/{delegation_id}/revoke", response_model=DelegationResponse)
def revoke_delegation(
    delegation_id: str,
    firm_id: str,
    delegations: DelegationEngine = Depends(get_delegation_engine),
) -> DelegationResponse:
    try:
        delegation = delegations.revoke(firm_id, delegation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _delegation_response(delegation)


def _secret_response(secret: ManagedSecret) -> SecretResponse:
    return SecretResponse(
        key=secret.key,
        firm_id=secret.firm_id,
        created_at=secret.created_at.isoformat(),
        rotated_at=secret.rotated_at.isoformat() if secret.rotated_at is not None else None,
    )


@router.put("/secrets", response_model=SecretResponse)
def set_secret(
    payload: SecretSetRequest, secrets: SecretManagerEngine = Depends(get_secret_manager_engine)
) -> SecretResponse:
    return _secret_response(secrets.set_secret(payload.firm_id, payload.key, payload.plaintext))


@router.get("/secrets", response_model=list[SecretResponse])
def list_secrets(
    firm_id: str, secrets: SecretManagerEngine = Depends(get_secret_manager_engine)
) -> list[SecretResponse]:
    return [_secret_response(s) for s in secrets.list_for_firm(firm_id)]


def _security_event_response(event: SecurityEvent) -> SecurityEventResponse:
    detail = {
        k: str(v) for k, v in dataclasses.asdict(event).items() if k not in _EVENT_COMMON_FIELDS
    }
    return SecurityEventResponse(
        event_type=event.event_type,
        firm_id=event.firm_id,
        occurred_at=event.occurred_at.isoformat(),
        detail=detail,
    )


@router.get("/security-events", response_model=list[SecurityEventResponse])
def list_security_events(
    firm_id: str,
    bus: SecurityEventBus = Depends(get_security_event_bus),
    _principal: Principal = Depends(require_role("firm_admin", "platform_admin")),
) -> list[SecurityEventResponse]:
    return [_security_event_response(e) for e in bus.history if e.firm_id == firm_id]


@router.get("/dashboard", response_model=IdentityDashboardResponse)
def get_dashboard(
    firm_id: str,
    monitoring: IdentityMonitoringEngine = Depends(get_identity_monitoring_engine),
    _principal: Principal = Depends(require_role("firm_admin", "platform_admin")),
) -> IdentityDashboardResponse:
    dashboard = monitoring.dashboard(firm_id)
    return IdentityDashboardResponse(
        firm_id=dashboard.firm_id,
        active_sessions=dashboard.active_sessions,
        mfa_enrolled_users=dashboard.mfa_enrolled_users,
        trusted_devices=dashboard.trusted_devices,
        active_delegations=dashboard.active_delegations,
        active_policies=dashboard.active_policies,
        security_events_total=dashboard.security_events_total,
        high_risk_events_last_24h=dashboard.high_risk_events_last_24h,
    )
