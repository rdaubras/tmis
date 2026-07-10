from tmis.cabinet_os.subscriptions.schemas import PlanTier
from tmis.platform.licensing.engine import LicenseEngine
from tmis.platform.licensing.schemas import features_for_plan
from tmis.platform.licensing.signing import LicenseKeySigner
from tmis.platform.licensing.store import InMemoryLicenseStore


def _engine() -> LicenseEngine:
    return LicenseEngine(InMemoryLicenseStore(), LicenseKeySigner("test-signing-secret"))


def test_issue_creates_a_license_with_plan_defaults() -> None:
    engine = _engine()

    license_ = engine.issue("firm-1", PlanTier.CABINET)

    assert license_.seats == 10
    assert license_.features == features_for_plan(PlanTier.CABINET)


def test_validate_accepts_a_freshly_issued_key() -> None:
    engine = _engine()
    license_ = engine.issue("firm-1", PlanTier.SOLO)

    result = engine.validate(license_.key)

    assert result.valid is True


def test_validate_rejects_a_tampered_key() -> None:
    engine = _engine()
    license_ = engine.issue("firm-1", PlanTier.SOLO)
    tampered = license_.key[:-1] + ("0" if license_.key[-1] != "0" else "1")

    result = engine.validate(tampered)

    assert result.valid is False
    assert "tamper" in result.reason.lower() or "invalid" in result.reason.lower()


def test_validate_rejects_a_key_signed_with_a_different_secret() -> None:
    engine = _engine()
    license_ = engine.issue("firm-1", PlanTier.SOLO)
    other_signer = LicenseKeySigner("a-completely-different-secret")
    forged = other_signer.sign("forged-payload")

    assert engine.validate(license_.key).valid is True
    assert engine.validate(forged).valid is False


def test_renew_extends_expiry_and_supersedes_the_old_key() -> None:
    engine = _engine()
    license_ = engine.issue("firm-1", PlanTier.CABINET, duration_days=30)

    renewed = engine.renew("firm-1", extension_days=30)

    assert renewed.expires_at > license_.expires_at
    assert engine.validate(license_.key).valid is False
    assert engine.validate(renewed.key).valid is True


def test_has_feature_reflects_the_firms_plan() -> None:
    engine = _engine()
    engine.issue("firm-1", PlanTier.ENTERPRISE)

    assert engine.has_feature("firm-1", "sso") is True
    assert engine.has_feature("firm-1", "nonexistent-feature") is False


def test_has_feature_is_false_when_no_license_exists() -> None:
    engine = _engine()

    assert engine.has_feature("firm-without-a-license", "billing") is False


def test_seats_remaining_accounts_for_current_usage() -> None:
    engine = _engine()
    engine.issue("firm-1", PlanTier.CABINET)

    assert engine.seats_remaining("firm-1", seats_in_use=3) == 7


def test_seats_remaining_never_goes_negative() -> None:
    engine = _engine()
    engine.issue("firm-1", PlanTier.SOLO)

    assert engine.seats_remaining("firm-1", seats_in_use=99) == 0
