import pytest

from tmis.cabinet_os.public_api.engine import PublicApiEngine
from tmis.cabinet_os.public_api.rate_limiter import InMemoryRateLimiter
from tmis.cabinet_os.public_api.schemas import ApiScope, RateLimitPolicy
from tmis.cabinet_os.public_api.security import hash_secret, key_prefix
from tmis.cabinet_os.public_api.store import (
    InMemoryApiKeyStore,
    InMemoryOAuthClientStore,
    InMemoryOAuthTokenStore,
)


def _engine(rate_limiter: InMemoryRateLimiter | None = None) -> PublicApiEngine:
    return PublicApiEngine(
        InMemoryApiKeyStore(),
        InMemoryOAuthClientStore(),
        InMemoryOAuthTokenStore(),
        rate_limiter or InMemoryRateLimiter(),
    )


def test_issue_api_key_returns_the_raw_key_once() -> None:
    engine = _engine()
    key, raw_key = engine.issue_api_key(
        "firm-1", "CRM integration", frozenset({ApiScope.READ_CLIENTS})
    )

    assert key.key_hash == hash_secret(raw_key)
    assert key.prefix == key_prefix(raw_key)


def test_authenticate_api_key_with_the_raw_key() -> None:
    engine = _engine()
    _, raw_key = engine.issue_api_key("firm-1", "Integration", frozenset({ApiScope.READ_CASES}))

    authenticated = engine.authenticate_api_key(raw_key)

    assert authenticated is not None
    assert authenticated.firm_id == "firm-1"
    assert authenticated.last_used_at is not None


def test_authenticate_wrong_key_returns_none() -> None:
    engine = _engine()
    engine.issue_api_key("firm-1", "Integration", frozenset({ApiScope.READ_CASES}))

    assert engine.authenticate_api_key("not-a-real-key") is None


def test_revoked_api_key_no_longer_authenticates() -> None:
    engine = _engine()
    key, raw_key = engine.issue_api_key("firm-1", "Integration", frozenset({ApiScope.READ_CASES}))

    engine.revoke_api_key(key.id)

    assert engine.authenticate_api_key(raw_key) is None


def test_revoke_unknown_key_raises() -> None:
    engine = _engine()
    with pytest.raises(ValueError, match="Unknown API key"):
        engine.revoke_api_key("nope")


def test_list_api_keys_scoped_per_firm() -> None:
    engine = _engine()
    engine.issue_api_key("firm-1", "A", frozenset({ApiScope.READ_CASES}))
    engine.issue_api_key("firm-2", "B", frozenset({ApiScope.READ_CASES}))

    assert len(engine.list_api_keys("firm-1")) == 1


def test_has_scope_matches_granted_scope() -> None:
    engine = _engine()
    assert engine.has_scope(frozenset({ApiScope.READ_CASES}), ApiScope.READ_CASES)
    assert not engine.has_scope(frozenset({ApiScope.READ_CASES}), ApiScope.WRITE_CASES)


def test_admin_scope_implies_every_other_scope() -> None:
    engine = _engine()
    assert engine.has_scope(frozenset({ApiScope.ADMIN}), ApiScope.WRITE_BILLING)


def test_oauth_client_credentials_flow_issues_a_token() -> None:
    engine = _engine()
    client, raw_secret = engine.register_oauth_client(
        "firm-1", ["https://client.example/callback"], frozenset({ApiScope.READ_DOCUMENTS})
    )

    token = engine.issue_oauth_token(client.client_id, raw_secret)

    assert engine.authenticate_oauth_token(token.token) is not None
    assert token.firm_id == "firm-1"


def test_oauth_token_issuance_with_wrong_secret_raises() -> None:
    engine = _engine()
    client, _ = engine.register_oauth_client(
        "firm-1", ["https://client.example/callback"], frozenset({ApiScope.READ_DOCUMENTS})
    )

    with pytest.raises(ValueError, match="Invalid OAuth client credentials"):
        engine.issue_oauth_token(client.client_id, "wrong-secret")


def test_authenticate_unknown_oauth_token_returns_none() -> None:
    engine = _engine()
    assert engine.authenticate_oauth_token("does-not-exist") is None


def test_rate_limiter_allows_within_policy() -> None:
    limiter = InMemoryRateLimiter(RateLimitPolicy(requests_per_minute=5, burst=0))
    for _ in range(5):
        result = limiter.check("key-1")
        assert result.allowed is True


def test_rate_limiter_blocks_beyond_policy() -> None:
    limiter = InMemoryRateLimiter(RateLimitPolicy(requests_per_minute=2, burst=0))
    limiter.check("key-1")
    limiter.check("key-1")

    result = limiter.check("key-1")

    assert result.allowed is False
    assert result.retry_after_seconds >= 0


def test_rate_limiter_tracks_identities_independently() -> None:
    limiter = InMemoryRateLimiter(RateLimitPolicy(requests_per_minute=1, burst=0))
    limiter.check("key-1")

    result_for_other_key = limiter.check("key-2")

    assert result_for_other_key.allowed is True


def test_check_rate_limit_delegates_to_the_limiter() -> None:
    engine = _engine(InMemoryRateLimiter(RateLimitPolicy(requests_per_minute=1, burst=0)))

    first = engine.check_rate_limit("client-1")
    second = engine.check_rate_limit("client-1")

    assert first.allowed is True
    assert second.allowed is False
