from functools import lru_cache

from tmis.identity_platform.abac.engine import AbacEngine
from tmis.identity_platform.abac.rules import (
    ConfidentialityRule,
    MinimumSeniorityRule,
    SameDepartmentRule,
)
from tmis.identity_platform.audit.engine import SecurityAuditEngine
from tmis.identity_platform.audit.store import InMemorySecurityAuditStore
from tmis.identity_platform.authentication.engine import AuthenticationEngine
from tmis.identity_platform.authorization.engine import AuthorizationEngine
from tmis.identity_platform.compliance.engine import IdentityComplianceEngine
from tmis.identity_platform.configuration.engine import IdentityConfigurationEngine
from tmis.identity_platform.configuration.store import InMemoryIdentityConfigurationStore
from tmis.identity_platform.delegation.engine import DelegationEngine
from tmis.identity_platform.delegation.store import InMemoryDelegationStore
from tmis.identity_platform.departments.engine import DepartmentEngine
from tmis.identity_platform.departments.store import InMemoryDepartmentStore
from tmis.identity_platform.device_trust.engine import DeviceTrustEngine
from tmis.identity_platform.device_trust.store import InMemoryDeviceStore
from tmis.identity_platform.identity_context.engine import IdentityContextEngine
from tmis.identity_platform.identity_context.store import InMemoryIdentityContextStore
from tmis.identity_platform.impersonation.engine import ImpersonationEngine
from tmis.identity_platform.impersonation.store import InMemoryImpersonationStore
from tmis.identity_platform.magic_links.engine import MagicLinkEngine
from tmis.identity_platform.magic_links.store import InMemoryUsedMagicLinkStore
from tmis.identity_platform.mfa.engine import MfaEngine
from tmis.identity_platform.mfa.store import InMemoryTotpEnrollmentStore
from tmis.identity_platform.monitoring.engine import IdentityMonitoringEngine
from tmis.identity_platform.oauth2.engine import OAuth2Engine
from tmis.identity_platform.oauth2.store import (
    InMemoryAuthorizationCodeStore,
    InMemoryOAuth2ClientStore,
)
from tmis.identity_platform.openid_connect.engine import OpenIdConnectEngine
from tmis.identity_platform.organization.engine import OrganizationEngine
from tmis.identity_platform.organization.store import InMemoryOrganizationStore
from tmis.identity_platform.passkeys.engine import PasskeyEngine
from tmis.identity_platform.passwordless.engine import PasswordlessEngine
from tmis.identity_platform.passwordless.store import InMemoryPasswordlessChallengeStore
from tmis.identity_platform.policy_engine.engine import PolicyEngine
from tmis.identity_platform.policy_engine.store import InMemoryPolicyStore
from tmis.identity_platform.rbac.engine import RbacEngine
from tmis.identity_platform.risk_engine.engine import RiskEngine
from tmis.identity_platform.roles.engine import RoleEngine
from tmis.identity_platform.roles.store import InMemoryRoleAssignmentStore
from tmis.identity_platform.secret_manager.engine import (
    SecretManagerEngine,
    new_rotating_encryption,
)
from tmis.identity_platform.secret_manager.store import InMemoryManagedSecretStore
from tmis.identity_platform.security_events.bus import SecurityEventBus
from tmis.identity_platform.session_manager.engine import SessionManager
from tmis.identity_platform.session_manager.store import InMemorySessionStore
from tmis.identity_platform.teams.engine import TeamEngine
from tmis.identity_platform.teams.store import InMemoryTeamStore
from tmis.identity_platform.tenant_context.engine import TenantContextEngine
from tmis.identity_platform.tenant_context.store import InMemoryTenantProfileStore
from tmis.identity_platform.tenant_management.engine import TenantManagementEngine
from tmis.identity_platform.users.engine import UserEngine
from tmis.identity_platform.users.store import InMemoryUserStore
from tmis.identity_platform.webauthn.engine import WebAuthnEngine
from tmis.identity_platform.webauthn.store import InMemoryWebAuthnCredentialStore
from tmis.platform.compliance.engine import ComplianceEngine
from tmis.platform.compliance.store import (
    InMemoryAccessLogStore,
    InMemoryConsentStore,
    InMemoryProcessingRegisterStore,
    InMemoryRetentionPolicyStore,
)
from tmis.platform.rate_limiting.brute_force import BruteForceProtector
from tmis.platform.security.secrets_rotation import InMemorySecretRotationStore

_CONFIDENTIALITY_EXPERIENCE_RANK = {"junior": 0, "senior": 1, "partner": 2}


@lru_cache
def get_tenant_context_engine() -> TenantContextEngine:
    """Process-wide composition root for `tmis.identity_platform` —
    the Enterprise Identity & Trust Platform every other module must
    pass through (see docs/103-architecture-identity-platform.md)."""
    return TenantContextEngine(InMemoryTenantProfileStore())


@lru_cache
def get_identity_context_engine() -> IdentityContextEngine:
    return IdentityContextEngine(InMemoryIdentityContextStore())


@lru_cache
def get_organization_engine() -> OrganizationEngine:
    return OrganizationEngine(InMemoryOrganizationStore())


@lru_cache
def get_department_engine() -> DepartmentEngine:
    return DepartmentEngine(InMemoryDepartmentStore())


@lru_cache
def get_team_engine() -> TeamEngine:
    return TeamEngine(InMemoryTeamStore())


@lru_cache
def get_user_engine() -> UserEngine:
    return UserEngine(InMemoryUserStore())


@lru_cache
def get_tenant_management_engine() -> TenantManagementEngine:
    return TenantManagementEngine(
        get_organization_engine(),
        get_department_engine(),
        get_team_engine(),
        get_user_engine(),
        get_tenant_context_engine(),
    )


@lru_cache
def get_role_engine() -> RoleEngine:
    return RoleEngine(InMemoryRoleAssignmentStore())


@lru_cache
def get_rbac_engine() -> RbacEngine:
    return RbacEngine()


@lru_cache
def get_abac_engine() -> AbacEngine:
    engine = AbacEngine()
    engine.register(MinimumSeniorityRule(min_years=0))
    engine.register(ConfidentialityRule(_CONFIDENTIALITY_EXPERIENCE_RANK))
    engine.register(SameDepartmentRule())
    return engine


@lru_cache
def get_policy_engine() -> PolicyEngine:
    return PolicyEngine(InMemoryPolicyStore())


@lru_cache
def get_authorization_engine() -> AuthorizationEngine:
    return AuthorizationEngine(
        get_role_engine(), get_rbac_engine(), get_abac_engine(), get_policy_engine()
    )


@lru_cache
def get_authentication_engine() -> AuthenticationEngine:
    return AuthenticationEngine()


@lru_cache
def get_oauth2_engine() -> OAuth2Engine:
    return OAuth2Engine(InMemoryOAuth2ClientStore(), InMemoryAuthorizationCodeStore())


@lru_cache
def get_openid_connect_engine() -> OpenIdConnectEngine:
    return OpenIdConnectEngine(get_oauth2_engine())


@lru_cache
def get_mfa_engine() -> MfaEngine:
    return MfaEngine(InMemoryTotpEnrollmentStore())


@lru_cache
def get_webauthn_credential_store() -> InMemoryWebAuthnCredentialStore:
    return InMemoryWebAuthnCredentialStore()


@lru_cache
def get_webauthn_engine() -> WebAuthnEngine:
    return WebAuthnEngine(get_webauthn_credential_store())


@lru_cache
def get_passkey_engine() -> PasskeyEngine:
    return PasskeyEngine(get_webauthn_engine(), get_webauthn_credential_store())


@lru_cache
def get_passwordless_engine() -> PasswordlessEngine:
    return PasswordlessEngine(InMemoryPasswordlessChallengeStore())


@lru_cache
def get_magic_link_engine() -> MagicLinkEngine:
    return MagicLinkEngine(InMemoryUsedMagicLinkStore())


@lru_cache
def get_session_manager() -> SessionManager:
    return SessionManager(InMemorySessionStore())


@lru_cache
def get_device_trust_engine() -> DeviceTrustEngine:
    return DeviceTrustEngine(InMemoryDeviceStore())


@lru_cache
def get_delegation_engine() -> DelegationEngine:
    return DelegationEngine(InMemoryDelegationStore())


@lru_cache
def get_impersonation_engine() -> ImpersonationEngine:
    return ImpersonationEngine(InMemoryImpersonationStore())


@lru_cache
def get_secret_manager_engine() -> SecretManagerEngine:
    rotation = new_rotating_encryption(InMemorySecretRotationStore())
    return SecretManagerEngine(InMemoryManagedSecretStore(), rotation)


@lru_cache
def get_security_event_bus() -> SecurityEventBus:
    return SecurityEventBus()


@lru_cache
def get_security_audit_engine() -> SecurityAuditEngine:
    return SecurityAuditEngine(InMemorySecurityAuditStore(), get_security_event_bus())


@lru_cache
def get_brute_force_protector() -> BruteForceProtector:
    return BruteForceProtector()


@lru_cache
def get_risk_engine() -> RiskEngine:
    return RiskEngine(get_device_trust_engine(), get_brute_force_protector())


@lru_cache
def get_platform_compliance_engine() -> ComplianceEngine:
    return ComplianceEngine(
        InMemoryAccessLogStore(),
        InMemoryRetentionPolicyStore(),
        InMemoryProcessingRegisterStore(),
        InMemoryConsentStore(),
    )


@lru_cache
def get_identity_compliance_engine() -> IdentityComplianceEngine:
    return IdentityComplianceEngine(
        get_platform_compliance_engine(),
        get_user_engine(),
        get_session_manager(),
        get_device_trust_engine(),
        get_delegation_engine(),
    )


@lru_cache
def get_identity_configuration_engine() -> IdentityConfigurationEngine:
    return IdentityConfigurationEngine(InMemoryIdentityConfigurationStore())


@lru_cache
def get_identity_monitoring_engine() -> IdentityMonitoringEngine:
    return IdentityMonitoringEngine(
        get_session_manager(),
        get_mfa_engine(),
        get_device_trust_engine(),
        get_delegation_engine(),
        get_policy_engine(),
        get_security_event_bus(),
    )
