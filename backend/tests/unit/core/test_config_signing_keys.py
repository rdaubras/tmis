import pytest

from tmis.core.config import Settings


@pytest.mark.parametrize("field_name", ["license_signing_key", "plugin_signing_key"])
def test_default_signing_key_outside_debug_refuses_to_start(field_name: str) -> None:
    with pytest.raises(RuntimeError, match=field_name.upper()):
        Settings(debug=False, jwt_secret_key="x" * 32, **{field_name: "change-me-in-production"})


@pytest.mark.parametrize("field_name", ["license_signing_key", "plugin_signing_key"])
def test_empty_signing_key_outside_debug_refuses_to_start(field_name: str) -> None:
    with pytest.raises(RuntimeError, match=field_name.upper()):
        Settings(debug=False, jwt_secret_key="x" * 32, **{field_name: ""})


def test_default_signing_keys_are_tolerated_in_debug_mode() -> None:
    settings = Settings(
        debug=True,
        jwt_secret_key="short",
        license_signing_key="change-me-in-production",
        plugin_signing_key="change-me-in-production",
    )

    assert settings.license_signing_key == "change-me-in-production"
    assert settings.plugin_signing_key == "change-me-in-production"


def test_real_signing_keys_are_accepted_outside_debug() -> None:
    settings = Settings(
        debug=False,
        jwt_secret_key="x" * 32,
        license_signing_key="a-real-license-key",
        plugin_signing_key="a-real-plugin-key",
    )

    assert settings.license_signing_key == "a-real-license-key"
    assert settings.plugin_signing_key == "a-real-plugin-key"
