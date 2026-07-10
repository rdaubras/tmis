from tmis.collaboration.permissions.engine import ConfigurablePermissionEngine
from tmis.collaboration.permissions.schemas import Permission
from tmis.collaboration.roles.schemas import Role
from tmis.collaboration.roles.store import InMemoryRoleAssignmentStore


def test_role_store_assigns_exactly_one_role_per_member() -> None:
    store = InMemoryRoleAssignmentStore()
    store.assign("ws-1", "member-1", Role.COLLABORATOR)
    store.assign("ws-1", "member-1", Role.ASSOCIATE)

    assert store.get_role("ws-1", "member-1") is Role.ASSOCIATE


def test_role_store_scopes_roles_per_workspace() -> None:
    store = InMemoryRoleAssignmentStore()
    store.assign("ws-1", "member-1", Role.ADMINISTRATOR)
    store.assign("ws-2", "member-1", Role.CLIENT)

    assert store.get_role("ws-1", "member-1") is Role.ADMINISTRATOR
    assert store.get_role("ws-2", "member-1") is Role.CLIENT


def test_role_store_list_by_role() -> None:
    store = InMemoryRoleAssignmentStore()
    store.assign("ws-1", "member-1", Role.JURIST)
    store.assign("ws-1", "member-2", Role.JURIST)
    store.assign("ws-1", "member-3", Role.ASSISTANT)

    jurists = store.list_by_role("ws-1", Role.JURIST)

    assert set(jurists) == {"member-1", "member-2"}


def test_administrator_has_every_permission_by_default() -> None:
    engine = ConfigurablePermissionEngine()

    for permission in Permission:
        assert engine.has_permission("ws-1", "admin-1", Role.ADMINISTRATOR, permission)


def test_client_role_is_read_only() -> None:
    engine = ConfigurablePermissionEngine()

    assert engine.has_permission("ws-1", "client-1", Role.CLIENT, Permission.CASE_READ)
    assert not engine.has_permission("ws-1", "client-1", Role.CLIENT, Permission.CASE_WRITE)
    assert not engine.has_permission("ws-1", "client-1", Role.CLIENT, Permission.TASK_CREATE)


def test_grant_override_adds_a_permission_beyond_the_role() -> None:
    engine = ConfigurablePermissionEngine()
    engine.grant_override("ws-1", "client-1", Permission.TASK_CREATE)

    assert engine.has_permission("ws-1", "client-1", Role.CLIENT, Permission.TASK_CREATE)


def test_revoke_override_wins_over_the_role_matrix() -> None:
    engine = ConfigurablePermissionEngine()

    assert engine.has_permission("ws-1", "admin-1", Role.ADMINISTRATOR, Permission.CASE_WRITE)

    engine.revoke_override("ws-1", "admin-1", Permission.CASE_WRITE)

    assert not engine.has_permission("ws-1", "admin-1", Role.ADMINISTRATOR, Permission.CASE_WRITE)


def test_revoke_override_wins_over_a_grant_override() -> None:
    """Deny-overrides precedence: revoking after granting must still deny —
    a member cannot restore access to themselves by re-granting first."""
    engine = ConfigurablePermissionEngine()
    engine.grant_override("ws-1", "client-1", Permission.CASE_WRITE)
    engine.revoke_override("ws-1", "client-1", Permission.CASE_WRITE)

    assert not engine.has_permission("ws-1", "client-1", Role.CLIENT, Permission.CASE_WRITE)


def test_grant_override_after_revoke_clears_the_revoke() -> None:
    engine = ConfigurablePermissionEngine()
    engine.revoke_override("ws-1", "admin-1", Permission.CASE_WRITE)
    engine.grant_override("ws-1", "admin-1", Permission.CASE_WRITE)

    assert engine.has_permission("ws-1", "admin-1", Role.ADMINISTRATOR, Permission.CASE_WRITE)


def test_overrides_are_scoped_per_member_and_workspace() -> None:
    engine = ConfigurablePermissionEngine()
    engine.revoke_override("ws-1", "admin-1", Permission.CASE_WRITE)

    assert engine.has_permission("ws-1", "admin-2", Role.ADMINISTRATOR, Permission.CASE_WRITE)
    assert engine.has_permission("ws-2", "admin-1", Role.ADMINISTRATOR, Permission.CASE_WRITE)


def test_set_role_permissions_reconfigures_the_matrix() -> None:
    engine = ConfigurablePermissionEngine()
    engine.set_role_permissions(Role.CLIENT, {Permission.CASE_READ, Permission.COMMENT_WRITE})

    assert engine.has_permission("ws-1", "client-1", Role.CLIENT, Permission.COMMENT_WRITE)
    assert not engine.has_permission("ws-1", "client-1", Role.CLIENT, Permission.DOCUMENT_READ)
