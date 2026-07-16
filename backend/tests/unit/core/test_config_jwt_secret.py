import pytest

from tmis.core.config import Settings


def test_short_secret_outside_debug_refuses_to_start() -> None:
    with pytest.raises(RuntimeError, match="TMIS_JWT_SECRET_KEY"):
        Settings(debug=False, jwt_secret_key="too-short")


def test_missing_secret_outside_debug_refuses_to_start() -> None:
    with pytest.raises(RuntimeError, match="TMIS_JWT_SECRET_KEY"):
        Settings(debug=False, jwt_secret_key="")


def test_short_secret_is_tolerated_in_debug_mode() -> None:
    settings = Settings(debug=True, jwt_secret_key="short")
    assert settings.jwt_secret_key == "short"


def test_strong_secret_is_accepted_outside_debug() -> None:
    settings = Settings(debug=False, jwt_secret_key="x" * 32)
    assert len(settings.jwt_secret_key) == 32
