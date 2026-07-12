from tmis.identity_platform.device_trust.engine import DeviceTrustEngine
from tmis.identity_platform.device_trust.store import InMemoryDeviceStore
from tmis.identity_platform.session_manager.engine import SessionManager
from tmis.identity_platform.session_manager.store import InMemorySessionStore


def test_session_lifecycle_create_revoke_rotate() -> None:
    manager = SessionManager(InMemorySessionStore())
    session = manager.create("firm-1", "user-1", device_id="device-1")

    assert manager.is_active("firm-1", session.id) is True

    old_token = session.refresh_token
    new_token = manager.rotate_refresh_token("firm-1", session.id)
    assert new_token != old_token

    manager.revoke("firm-1", session.id)
    assert manager.is_active("firm-1", session.id) is False


def test_revoke_all_for_user_revokes_every_session() -> None:
    manager = SessionManager(InMemorySessionStore())
    manager.create("firm-1", "user-1")
    manager.create("firm-1", "user-1")
    manager.create("firm-1", "user-2")

    revoked = manager.revoke_all_for_user("firm-1", "user-1")

    assert len(revoked) == 2
    assert all(s.revoked for s in manager.list_for_user("firm-1", "user-1"))
    assert not manager.list_for_user("firm-1", "user-2")[0].revoked


def test_list_for_firm_returns_every_session_regardless_of_user() -> None:
    manager = SessionManager(InMemorySessionStore())
    manager.create("firm-1", "user-1")
    manager.create("firm-1", "user-2")
    manager.create("firm-2", "user-3")

    assert len(manager.list_for_firm("firm-1")) == 2
    assert len(manager.list_for_firm("firm-2")) == 1


def test_device_starts_unknown_and_must_be_explicitly_trusted() -> None:
    engine = DeviceTrustEngine(InMemoryDeviceStore())
    device = engine.register("firm-1", "user-1", "Laptop pro")

    assert engine.is_trusted("firm-1", device.id) is False

    engine.trust("firm-1", device.id)
    assert engine.is_trusted("firm-1", device.id) is True

    engine.revoke("firm-1", device.id)
    assert engine.is_trusted("firm-1", device.id) is False


def test_device_list_for_firm_aggregates_across_users() -> None:
    engine = DeviceTrustEngine(InMemoryDeviceStore())
    engine.register("firm-1", "user-1", "Laptop")
    engine.register("firm-1", "user-2", "Phone")
    engine.register("firm-2", "user-3", "Tablet")

    assert len(engine.list_for_firm("firm-1")) == 2
    assert len(engine.list_for_firm("firm-2")) == 1
