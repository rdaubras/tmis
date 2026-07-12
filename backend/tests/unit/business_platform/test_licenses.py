import pytest

from tmis.business_platform.licenses.engine import FloatingPoolExhaustedError, LicenseEngine
from tmis.business_platform.licenses.schemas import LicenseType
from tmis.business_platform.licenses.store import (
    InMemoryFloatingPoolStore,
    InMemoryLicenseGrantStore,
)
from tmis.platform.licensing.signing import LicenseKeySigner


def _engine() -> LicenseEngine:
    return LicenseEngine(
        InMemoryLicenseGrantStore(),
        InMemoryFloatingPoolStore(),
        LicenseKeySigner(secret="test-secret-0123456789abcdef"),
    )


def test_assign_produces_a_signed_key_that_validates() -> None:
    engine = _engine()

    grant = engine.assign("firm-1", LicenseType.NOMINATIVE, holder_id="user-1")

    assert engine.validate(grant.key) is True
    assert grant.is_active() is True


def test_revoke_makes_grant_inactive() -> None:
    engine = _engine()
    grant = engine.assign("firm-1", LicenseType.API, holder_id="client-1")

    engine.revoke("firm-1", grant.id)

    assert engine.active_grants_for_firm("firm-1") == []


def test_transfer_issues_new_grant_and_revokes_the_old_one() -> None:
    engine = _engine()
    grant = engine.assign("firm-1", LicenseType.GUEST, holder_id="user-1")

    transferred = engine.transfer("firm-1", grant.id, new_holder_id="user-2")

    active_ids = {g.id for g in engine.active_grants_for_firm("firm-1")}
    assert transferred.holder_id == "user-2"
    assert transferred.transferred_from == grant.id
    assert transferred.id in active_ids
    assert grant.id not in active_ids


def test_floating_pool_checkout_respects_capacity() -> None:
    engine = _engine()
    engine.set_floating_pool_capacity("firm-1", total_seats=1)
    engine.checkout_floating("firm-1", holder_id="user-1")

    with pytest.raises(FloatingPoolExhaustedError):
        engine.checkout_floating("firm-1", holder_id="user-2")


def test_floating_checkin_frees_a_seat() -> None:
    engine = _engine()
    engine.set_floating_pool_capacity("firm-1", total_seats=1)
    grant = engine.checkout_floating("firm-1", holder_id="user-1")

    engine.checkin_floating("firm-1", grant.id)
    reassigned = engine.checkout_floating("firm-1", holder_id="user-2")

    assert reassigned.holder_id == "user-2"


def test_active_grants_for_holder_filters_by_holder() -> None:
    engine = _engine()
    engine.assign("firm-1", LicenseType.NOMINATIVE, holder_id="user-1")
    engine.assign("firm-1", LicenseType.NOMINATIVE, holder_id="user-2")

    grants = engine.active_grants_for_holder("firm-1", "user-1")

    assert len(grants) == 1
    assert grants[0].holder_id == "user-1"
