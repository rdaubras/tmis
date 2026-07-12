from datetime import UTC, datetime, timedelta

import pytest

from tmis.identity_platform.delegation.engine import DelegationEngine
from tmis.identity_platform.delegation.store import InMemoryDelegationStore
from tmis.identity_platform.impersonation.engine import ImpersonationEngine
from tmis.identity_platform.impersonation.store import InMemoryImpersonationStore
from tmis.identity_platform.permissions.schemas import Permission


def test_delegation_is_active_only_within_its_time_window() -> None:
    engine = DelegationEngine(InMemoryDelegationStore())
    now = datetime.now(UTC)
    delegation = engine.grant(
        "firm-1",
        delegator_id="partner-1",
        delegate_id="collaborator-1",
        permissions=frozenset({Permission.CONSULTATION_VALIDATE}),
        ends_at=now + timedelta(days=1),
    )

    check_now = now + timedelta(seconds=1)
    assert engine.has_delegated_permission(
        "firm-1", "collaborator-1", Permission.CONSULTATION_VALIDATE, now=check_now
    )
    assert not engine.has_delegated_permission(
        "firm-1",
        "collaborator-1",
        Permission.CONSULTATION_VALIDATE,
        now=check_now + timedelta(days=2),
    )

    engine.revoke("firm-1", delegation.id)
    assert not engine.has_delegated_permission(
        "firm-1", "collaborator-1", Permission.CONSULTATION_VALIDATE, now=check_now
    )


def test_delegation_never_grants_a_permission_outside_its_scope() -> None:
    engine = DelegationEngine(InMemoryDelegationStore())
    engine.grant(
        "firm-1",
        delegator_id="partner-1",
        delegate_id="collaborator-1",
        permissions=frozenset({Permission.CONSULTATION_VALIDATE}),
        ends_at=datetime.now(UTC) + timedelta(days=1),
    )

    assert not engine.has_delegated_permission("firm-1", "collaborator-1", Permission.EXPORT_DATA)


def test_active_delegations_for_firm_aggregates_across_delegates() -> None:
    engine = DelegationEngine(InMemoryDelegationStore())
    ends_at = datetime.now(UTC) + timedelta(days=1)
    engine.grant("firm-1", "partner-1", "collab-1", frozenset({Permission.EXPORT_DATA}), ends_at)
    engine.grant("firm-1", "partner-2", "collab-2", frozenset({Permission.EXPORT_DATA}), ends_at)
    engine.grant("firm-2", "partner-3", "collab-3", frozenset({Permission.EXPORT_DATA}), ends_at)

    assert len(engine.active_delegations_for_firm("firm-1")) == 2
    assert len(engine.active_delegations_for_firm("firm-2")) == 1


def test_impersonation_refuses_concurrent_sessions_for_the_same_admin() -> None:
    engine = ImpersonationEngine(InMemoryImpersonationStore())
    engine.start("firm-1", "admin-1", "user-1", "support ticket #42")

    with pytest.raises(RuntimeError):
        engine.start("firm-1", "admin-1", "user-2", "another ticket")


def test_impersonation_history_never_loses_ended_sessions() -> None:
    engine = ImpersonationEngine(InMemoryImpersonationStore())
    session = engine.start("firm-1", "admin-1", "user-1", "support ticket #42")

    assert engine.active_for_admin("firm-1", "admin-1") is not None
    engine.end("firm-1", session.id)
    assert engine.active_for_admin("firm-1", "admin-1") is None

    history = engine.history("firm-1")
    assert len(history) == 1
    assert history[0].ended_at is not None
