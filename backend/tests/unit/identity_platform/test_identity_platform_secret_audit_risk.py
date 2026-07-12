import asyncio

from tmis.identity_platform.audit.engine import SecurityAuditEngine
from tmis.identity_platform.audit.store import InMemorySecurityAuditStore
from tmis.identity_platform.device_trust.engine import DeviceTrustEngine
from tmis.identity_platform.device_trust.store import InMemoryDeviceStore
from tmis.identity_platform.risk_engine.engine import RiskEngine
from tmis.identity_platform.risk_engine.schemas import RiskLevel
from tmis.identity_platform.secret_manager.engine import (
    SecretManagerEngine,
    new_rotating_encryption,
)
from tmis.identity_platform.secret_manager.store import InMemoryManagedSecretStore
from tmis.identity_platform.security_events.bus import SecurityEventBus
from tmis.identity_platform.security_events.schemas import LoginFailed, LoginSucceeded
from tmis.platform.rate_limiting.brute_force import BruteForceProtector
from tmis.platform.rate_limiting.schemas import LockoutPolicy
from tmis.platform.security.secrets_rotation import InMemorySecretRotationStore


def test_secret_manager_never_stores_plaintext() -> None:
    rotation = new_rotating_encryption(InMemorySecretRotationStore())
    engine = SecretManagerEngine(InMemoryManagedSecretStore(), rotation)

    secret = engine.set_secret("firm-1", "crm-api-key", "super-secret-value")

    assert "super-secret-value" not in secret.encrypted_value
    assert engine.get_secret("firm-1", "crm-api-key") == "super-secret-value"


def test_secret_manager_list_for_firm_exposes_metadata_only() -> None:
    rotation = new_rotating_encryption(InMemorySecretRotationStore())
    engine = SecretManagerEngine(InMemoryManagedSecretStore(), rotation)
    engine.set_secret("firm-1", "key-a", "value-a")
    engine.set_secret("firm-2", "key-b", "value-b")

    secrets = engine.list_for_firm("firm-1")

    assert [s.key for s in secrets] == ["key-a"]
    assert all("value-a" not in s.encrypted_value for s in secrets)


def test_security_event_bus_subscribe_all_receives_every_event_type() -> None:
    bus = SecurityEventBus()
    received: list[str] = []

    async def handler(event: object) -> None:
        received.append(type(event).__name__)

    bus.subscribe_all(handler)

    asyncio.run(bus.publish(LoginSucceeded(firm_id="firm-1", user_id="user-1", method="oauth2")))
    asyncio.run(bus.publish(LoginFailed(firm_id="firm-1", identity="user-2", reason="bad code")))

    assert received == ["LoginSucceeded", "LoginFailed"]
    assert len(bus.history) == 2


def test_audit_engine_builds_trail_from_bus_without_a_manual_subscription_per_event() -> None:
    bus = SecurityEventBus()
    audit = SecurityAuditEngine(InMemorySecurityAuditStore(), bus)

    asyncio.run(bus.publish(LoginSucceeded(firm_id="firm-1", user_id="user-1", method="oauth2")))
    asyncio.run(bus.publish(LoginFailed(firm_id="firm-2", identity="user-x", reason="mfa failed")))

    firm_1_trail = audit.list_for_firm("firm-1")
    assert len(firm_1_trail) == 1
    assert firm_1_trail[0].event_type == "LoginSucceeded"
    assert "user_id=user-1" in firm_1_trail[0].summary


def test_risk_engine_flags_unknown_device_as_medium_risk() -> None:
    devices = DeviceTrustEngine(InMemoryDeviceStore())
    risk = RiskEngine(devices, BruteForceProtector())

    assessment = risk.assess_login("firm-1", "user-1", device_id=None)

    assert assessment.level is RiskLevel.MEDIUM
    assert assessment.requires_step_up_mfa is True


def test_risk_engine_is_low_risk_for_a_trusted_device_with_no_failures() -> None:
    devices = DeviceTrustEngine(InMemoryDeviceStore())
    device = devices.register("firm-1", "user-1", "Laptop")
    devices.trust("firm-1", device.id)
    risk = RiskEngine(devices, BruteForceProtector())

    assessment = risk.assess_login("firm-1", "user-1", device_id=device.id)

    assert assessment.level is RiskLevel.LOW
    assert assessment.requires_step_up_mfa is False


def test_risk_engine_escalates_to_high_after_lockout_threshold() -> None:
    devices = DeviceTrustEngine(InMemoryDeviceStore())
    protector = BruteForceProtector(LockoutPolicy(max_failed_attempts=2))
    risk = RiskEngine(devices, protector)

    risk.record_failure("firm-1", "user-1")
    risk.record_failure("firm-1", "user-1")

    assessment = risk.assess_login("firm-1", "user-1", device_id=None)

    assert assessment.level is RiskLevel.HIGH
