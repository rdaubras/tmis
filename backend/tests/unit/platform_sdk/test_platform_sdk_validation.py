from tmis.platform.licensing.signing import LicenseKeySigner
from tmis.platform_sdk.plugin_registry.store import InMemoryPluginRegistry
from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PluginType
from tmis.platform_sdk.validation.engine import PluginValidator
from tmis.platform_sdk.validation.schemas import SDK_VERSION


def _manifest(**overrides: object) -> PluginManifest:
    defaults: dict[str, object] = {
        "id": "p1",
        "name": "Plugin 1",
        "version": "1.0.0",
        "plugin_type": PluginType.AGENT,
        "author": "a",
        "description": "...",
        "license": "MIT",
    }
    defaults.update(overrides)
    return PluginManifest(**defaults)  # type: ignore[arg-type]


def _validator(registry: InMemoryPluginRegistry | None = None) -> PluginValidator:
    return PluginValidator(registry or InMemoryPluginRegistry(), LicenseKeySigner("test-secret"))


def test_valid_manifest_has_no_issues() -> None:
    report = _validator().validate(_manifest())

    assert report.is_valid


def test_missing_fields_are_reported() -> None:
    manifest = _manifest(name="", license="")

    report = _validator().validate(manifest)

    fields = {i.field for i in report.issues}
    assert {"name", "license"} <= fields


def test_unknown_permission_is_reported() -> None:
    manifest = _manifest(permissions=frozenset({"delete_everything"}))

    report = _validator().validate(manifest)

    assert any(i.field == "permissions" for i in report.issues)


def test_incompatible_sdk_version_is_reported() -> None:
    manifest = _manifest(compatibility="99.0.0")

    report = _validator().validate(manifest)

    assert any(i.field == "compatibility" for i in report.issues)


def test_wildcard_and_exact_compatibility_are_accepted() -> None:
    for compat in ("*", SDK_VERSION):
        report = _validator().validate(_manifest(compatibility=compat))
        assert not any(i.field == "compatibility" for i in report.issues)


def test_missing_dependency_is_reported() -> None:
    manifest = _manifest(dependencies=("does-not-exist",))

    report = _validator().validate(manifest)

    assert any(i.field == "dependencies" for i in report.issues)


def test_self_dependency_is_reported() -> None:
    manifest = _manifest(dependencies=("p1",))

    report = _validator().validate(manifest)

    assert any(i.field == "dependencies" for i in report.issues)


def test_circular_dependency_is_reported() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest(id="a", dependencies=("b",)))
    registry.register(_manifest(id="b", dependencies=("a",)))
    validator = _validator(registry)

    report = validator.validate(registry.get("a"))  # type: ignore[arg-type]

    assert any(i.field == "dependencies" for i in report.issues)


def test_valid_dependency_chain_has_no_issues() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest(id="base"))
    registry.register(_manifest(id="dependent", dependencies=("base",)))
    validator = _validator(registry)

    report = validator.validate(registry.get("dependent"))  # type: ignore[arg-type]

    assert report.is_valid


def test_sign_then_verify_succeeds() -> None:
    validator = _validator()
    manifest = _manifest()

    manifest.signature = validator.sign(manifest)

    assert validator.verify_signature(manifest) is True


def test_tampered_signature_fails_verification() -> None:
    validator = _validator()
    manifest = _manifest()
    manifest.signature = validator.sign(manifest)
    manifest.version = "2.0.0"

    assert validator.verify_signature(manifest) is False


def test_validate_reports_invalid_signature() -> None:
    validator = _validator()
    manifest = _manifest(signature="not-a-real-signature")

    report = validator.validate(manifest)

    assert any(i.field == "signature" for i in report.issues)
