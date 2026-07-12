from tmis.identity_platform.magic_links.engine import MagicLinkEngine
from tmis.identity_platform.magic_links.store import InMemoryUsedMagicLinkStore
from tmis.identity_platform.mfa.engine import MfaEngine
from tmis.identity_platform.mfa.store import InMemoryTotpEnrollmentStore
from tmis.identity_platform.mfa.totp import generate_totp
from tmis.identity_platform.passkeys.engine import PasskeyEngine
from tmis.identity_platform.passwordless.engine import PasswordlessEngine
from tmis.identity_platform.passwordless.store import InMemoryPasswordlessChallengeStore
from tmis.identity_platform.webauthn.engine import WebAuthnEngine
from tmis.identity_platform.webauthn.store import InMemoryWebAuthnCredentialStore


def test_mfa_enrollment_stays_unconfirmed_until_a_valid_code_is_proven() -> None:
    engine = MfaEngine(InMemoryTotpEnrollmentStore())
    enrollment = engine.enroll("firm-1", "user-1")

    assert engine.verify("firm-1", "user-1", generate_totp(enrollment.secret)) is False

    assert engine.confirm("firm-1", "user-1", "000000") is False
    assert engine.confirm("firm-1", "user-1", generate_totp(enrollment.secret)) is True
    assert engine.verify("firm-1", "user-1", generate_totp(enrollment.secret)) is True


def test_mfa_count_confirmed_for_firm_only_counts_confirmed_enrollments() -> None:
    engine = MfaEngine(InMemoryTotpEnrollmentStore())
    a = engine.enroll("firm-1", "user-a")
    engine.enroll("firm-1", "user-b")
    engine.confirm("firm-1", "user-a", generate_totp(a.secret))

    assert engine.count_confirmed_for_firm("firm-1") == 1


def test_webauthn_signature_counter_rejects_replay() -> None:
    engine = WebAuthnEngine(InMemoryWebAuthnCredentialStore())
    engine.register_credential("firm-1", "user-1", "cred-1", "opaque-public-key")

    assert engine.verify_assertion("firm-1", "cred-1", 1) is True
    assert engine.verify_assertion("firm-1", "cred-1", 1) is False
    assert engine.verify_assertion("firm-1", "cred-1", 2) is True


def test_passkey_authenticate_resolves_user_from_credential() -> None:
    store = InMemoryWebAuthnCredentialStore()
    webauthn = WebAuthnEngine(store)
    passkeys = PasskeyEngine(webauthn, store)
    webauthn.register_credential("firm-1", "user-1", "cred-1", "opaque-public-key")

    resolved = passkeys.authenticate("firm-1", "cred-1", 1)

    assert resolved == "user-1"
    assert passkeys.authenticate("firm-1", "cred-1", 1) is None


def test_passwordless_code_is_single_use_and_time_bound() -> None:
    engine = PasswordlessEngine(InMemoryPasswordlessChallengeStore())
    challenge = engine.request("firm-1", "user-1")

    assert engine.verify("firm-1", challenge.id, "000000") is None
    assert engine.verify("firm-1", challenge.id, challenge.code) == "user-1"
    assert engine.verify("firm-1", challenge.id, challenge.code) is None


def test_magic_link_token_is_single_use() -> None:
    engine = MagicLinkEngine(InMemoryUsedMagicLinkStore())
    token = engine.issue("firm-1", "user-1")

    assert engine.consume(token) == "user-1"
    assert engine.consume(token) is None


def test_magic_link_rejects_tokens_not_carrying_the_magic_link_purpose() -> None:
    from tmis.core.security import create_access_token

    engine = MagicLinkEngine(InMemoryUsedMagicLinkStore())
    unrelated_token = create_access_token("user-1", {"firm_id": "firm-1"})

    assert engine.consume(unrelated_token) is None
