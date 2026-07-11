from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.schemas import ExtensionPermission
from tmis.platform_sdk.permissions.store import InMemoryPermissionStore

FIRM = "firm-a"
PLUGIN = "plugin-1"


def _engine() -> PermissionEngine:
    return PermissionEngine(InMemoryPermissionStore())


def test_check_is_false_before_any_grant() -> None:
    engine = _engine()

    assert engine.check(FIRM, PLUGIN, ExtensionPermission.READ_CASES) is False


def test_grant_then_check() -> None:
    engine = _engine()
    engine.grant(FIRM, PLUGIN, frozenset({ExtensionPermission.READ_CASES}))

    assert engine.check(FIRM, PLUGIN, ExtensionPermission.READ_CASES) is True
    assert engine.check(FIRM, PLUGIN, ExtensionPermission.MANAGE_USERS) is False


def test_revoke_removes_all_permissions() -> None:
    engine = _engine()
    engine.grant(FIRM, PLUGIN, frozenset({ExtensionPermission.READ_CASES}))

    engine.revoke(FIRM, PLUGIN)

    assert engine.granted(FIRM, PLUGIN) == frozenset()


def test_permissions_are_scoped_per_firm_and_plugin() -> None:
    engine = _engine()
    engine.grant(FIRM, PLUGIN, frozenset({ExtensionPermission.READ_CASES}))

    assert engine.check("other-firm", PLUGIN, ExtensionPermission.READ_CASES) is False


def test_checker_for_exposes_scoped_has_permission() -> None:
    engine = _engine()
    engine.grant(FIRM, PLUGIN, frozenset({ExtensionPermission.CREATE_DRAFTS}))

    checker = engine.checker_for(FIRM, PLUGIN)

    assert checker.has_permission("create_drafts") is True
    assert checker.has_permission("manage_users") is False
