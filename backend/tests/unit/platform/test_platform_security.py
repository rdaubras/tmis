import pytest

from tmis.platform.security.encryption import FernetEncryption, generate_key
from tmis.platform.security.headers import (
    CORS_ALLOWED_HEADERS,
    CORS_ALLOWED_METHODS,
    validate_cors_origins,
)
from tmis.platform.security.secrets_rotation import InMemorySecretRotationStore, RotatingEncryption
from tmis.platform.security.tenant_isolation import (
    TenantAccessError,
    TenantContext,
    assert_tenant_isolated,
    require_same_firm,
)


def test_fernet_encryption_round_trips() -> None:
    encryption = FernetEncryption(generate_key())
    ciphertext = encryption.encrypt(b"privileged client memo")

    assert ciphertext != b"privileged client memo"
    assert encryption.decrypt(ciphertext) == b"privileged client memo"


def test_fernet_encryption_rejects_tampered_ciphertext() -> None:
    encryption = FernetEncryption(generate_key())
    ciphertext = bytearray(encryption.encrypt(b"secret"))
    ciphertext[-1] ^= 0xFF

    with pytest.raises(ValueError, match="tampered"):
        encryption.decrypt(bytes(ciphertext))


def test_validate_cors_origins_rejects_wildcard() -> None:
    with pytest.raises(ValueError, match="[Ww]ildcard"):
        validate_cors_origins(["*"])


def test_validate_cors_origins_accepts_explicit_origins() -> None:
    origins = validate_cors_origins(["https://app.tmis.example.com"])

    assert origins == ["https://app.tmis.example.com"]


def test_cors_allowed_methods_and_headers_are_non_empty() -> None:
    assert "GET" in CORS_ALLOWED_METHODS
    assert "Authorization" in CORS_ALLOWED_HEADERS


def test_rotating_encryption_decrypts_ciphertext_from_a_prior_key_version() -> None:
    store = InMemorySecretRotationStore()
    rotating = RotatingEncryption(store)

    old_ciphertext = rotating.encrypt(b"case note v1")
    store.rotate()
    new_ciphertext = rotating.encrypt(b"case note v2")

    assert rotating.decrypt(old_ciphertext) == b"case note v1"
    assert rotating.decrypt(new_ciphertext) == b"case note v2"
    assert old_ciphertext != new_ciphertext


def test_secret_rotation_store_keeps_every_version() -> None:
    store = InMemorySecretRotationStore()
    first = store.current()
    second = store.rotate()

    versions = store.list_versions()

    assert first in versions
    assert second in versions
    assert store.current() == second


def test_require_same_firm_allows_matching_firm() -> None:
    context = TenantContext(firm_id="firm-1", actor_id="user-1")

    require_same_firm(context, "firm-1")


def test_require_same_firm_blocks_cross_firm_access() -> None:
    context = TenantContext(firm_id="firm-1", actor_id="user-1")

    with pytest.raises(TenantAccessError):
        require_same_firm(context, "firm-2")


def test_assert_tenant_isolated_passes_when_every_record_belongs_to_the_firm() -> None:
    records = [{"firm_id": "firm-1"}, {"firm_id": "firm-1"}]

    assert_tenant_isolated(records, lambda r: r["firm_id"], "firm-1")


def test_assert_tenant_isolated_raises_on_a_leaked_cross_firm_record() -> None:
    records = [{"firm_id": "firm-1"}, {"firm_id": "firm-2"}]

    with pytest.raises(AssertionError):
        assert_tenant_isolated(records, lambda r: r["firm_id"], "firm-1")
