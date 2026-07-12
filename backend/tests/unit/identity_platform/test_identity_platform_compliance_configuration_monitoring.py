import asyncio
from datetime import UTC, datetime, timedelta

from tmis.identity_platform.authentication.schemas import AuthMethod
from tmis.identity_platform.compliance.engine import IdentityComplianceEngine
from tmis.identity_platform.configuration.engine import IdentityConfigurationEngine
from tmis.identity_platform.configuration.store import InMemoryIdentityConfigurationStore
from tmis.identity_platform.delegation.engine import DelegationEngine
from tmis.identity_platform.delegation.store import InMemoryDelegationStore
from tmis.identity_platform.device_trust.engine import DeviceTrustEngine
from tmis.identity_platform.device_trust.store import InMemoryDeviceStore
from tmis.identity_platform.mfa.engine import MfaEngine
from tmis.identity_platform.mfa.store import InMemoryTotpEnrollmentStore
from tmis.identity_platform.mfa.totp import generate_totp
from tmis.identity_platform.monitoring.engine import IdentityMonitoringEngine
from tmis.identity_platform.permissions.schemas import Permission
from tmis.identity_platform.policy_engine.engine import PolicyEngine
from tmis.identity_platform.policy_engine.store import InMemoryPolicyStore
from tmis.identity_platform.security_events.bus import SecurityEventBus
from tmis.identity_platform.security_events.schemas import LoginFailed
from tmis.identity_platform.session_manager.engine import SessionManager
from tmis.identity_platform.session_manager.store import InMemorySessionStore
from tmis.identity_platform.users.engine import UserEngine
from tmis.identity_platform.users.store import InMemoryUserStore
from tmis.platform.compliance.engine import ComplianceEngine
from tmis.platform.compliance.store import (
    InMemoryAccessLogStore,
    InMemoryConsentStore,
    InMemoryProcessingRegisterStore,
    InMemoryRetentionPolicyStore,
)


def _compliance_engine() -> ComplianceEngine:
    return ComplianceEngine(
        InMemoryAccessLogStore(),
        InMemoryRetentionPolicyStore(),
        InMemoryProcessingRegisterStore(),
        InMemoryConsentStore(),
    )


def test_identity_compliance_registers_identity_sources_not_reimplemented() -> None:
    users = UserEngine(InMemoryUserStore())
    sessions = SessionManager(InMemorySessionStore())
    devices = DeviceTrustEngine(InMemoryDeviceStore())
    delegations = DelegationEngine(InMemoryDelegationStore())
    compliance = _compliance_engine()
    identity_compliance = IdentityComplianceEngine(
        compliance, users, sessions, devices, delegations
    )

    user = users.create("firm-1", "user@example.com", "User One")
    sessions.create("firm-1", user.id)
    device = devices.register("firm-1", user.id, "Laptop")
    devices.trust("firm-1", device.id)

    bundle = identity_compliance.export_subject_data("firm-1", user.id)

    assert bundle.sections["identity_users"][0]["email"] == "user@example.com"
    assert len(bundle.sections["identity_sessions"]) == 1
    assert len(bundle.sections["identity_devices"]) == 1


def test_identity_compliance_deletion_deactivates_and_revokes() -> None:
    users = UserEngine(InMemoryUserStore())
    sessions = SessionManager(InMemorySessionStore())
    devices = DeviceTrustEngine(InMemoryDeviceStore())
    delegations = DelegationEngine(InMemoryDelegationStore())
    compliance = _compliance_engine()
    identity_compliance = IdentityComplianceEngine(
        compliance, users, sessions, devices, delegations
    )

    user = users.create("firm-1", "user@example.com", "User One")
    session = sessions.create("firm-1", user.id)

    receipt = identity_compliance.delete_subject_data("firm-1", user.id)

    assert "identity_users" in receipt.deleted_from
    assert users.get("firm-1", user.id).status.value == "deactivated"
    assert sessions.is_active("firm-1", session.id) is False


def test_identity_configuration_defaults_and_overrides() -> None:
    engine = IdentityConfigurationEngine(InMemoryIdentityConfigurationStore())

    config = engine.get_or_default("firm-1")
    assert config.mfa_required is False
    assert AuthMethod.OAUTH2 in config.allowed_auth_methods

    engine.set_mfa_required("firm-1", True)
    assert engine.get_or_default("firm-1").mfa_required is True

    engine.set_allowed_auth_methods("firm-1", frozenset({AuthMethod.WEBAUTHN}))
    assert engine.is_auth_method_allowed("firm-1", AuthMethod.WEBAUTHN) is True
    assert engine.is_auth_method_allowed("firm-1", AuthMethod.OAUTH2) is False


def test_identity_dashboard_aggregates_every_composed_engine() -> None:
    sessions = SessionManager(InMemorySessionStore())
    mfa = MfaEngine(InMemoryTotpEnrollmentStore())
    devices = DeviceTrustEngine(InMemoryDeviceStore())
    delegations = DelegationEngine(InMemoryDelegationStore())
    policies = PolicyEngine(InMemoryPolicyStore())
    events = SecurityEventBus()
    monitoring = IdentityMonitoringEngine(sessions, mfa, devices, delegations, policies, events)

    sessions.create("firm-1", "user-1")
    enrollment = mfa.enroll("firm-1", "user-1")
    mfa.confirm("firm-1", "user-1", generate_totp(enrollment.secret))
    device = devices.register("firm-1", "user-1", "Laptop")
    devices.trust("firm-1", device.id)
    delegations.grant(
        "firm-1",
        "user-1",
        "user-2",
        frozenset({Permission.EXPORT_DATA}),
        datetime.now(UTC) + timedelta(days=1),
    )
    policies.create("firm-1", Permission.EXPORT_DATA, denied_roles=frozenset())
    asyncio.run(events.publish(LoginFailed(firm_id="firm-1", identity="user-3", reason="bad")))

    dashboard = monitoring.dashboard("firm-1")

    assert dashboard.active_sessions == 1
    assert dashboard.mfa_enrolled_users == 1
    assert dashboard.trusted_devices == 1
    assert dashboard.active_delegations == 1
    assert dashboard.active_policies == 1
    assert dashboard.security_events_total == 1
    assert dashboard.high_risk_events_last_24h == 1


def test_identity_dashboard_is_scoped_to_a_single_firm() -> None:
    sessions = SessionManager(InMemorySessionStore())
    mfa = MfaEngine(InMemoryTotpEnrollmentStore())
    devices = DeviceTrustEngine(InMemoryDeviceStore())
    delegations = DelegationEngine(InMemoryDelegationStore())
    policies = PolicyEngine(InMemoryPolicyStore())
    events = SecurityEventBus()
    monitoring = IdentityMonitoringEngine(sessions, mfa, devices, delegations, policies, events)

    sessions.create("firm-1", "user-1")
    sessions.create("firm-2", "user-2")
    sessions.create("firm-2", "user-3")

    assert monitoring.dashboard("firm-1").active_sessions == 1
    assert monitoring.dashboard("firm-2").active_sessions == 2
