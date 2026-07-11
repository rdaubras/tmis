from tmis.platform.licensing.signing import LicenseKeySigner
from tmis.platform_sdk.permissions.schemas import ExtensionPermission
from tmis.platform_sdk.plugin_registry.ports import PluginRegistryPort
from tmis.platform_sdk.plugin_system.schemas import PluginManifest
from tmis.platform_sdk.validation.schemas import SDK_VERSION, ValidationIssue, ValidationReport


def _canonical_payload(manifest: PluginManifest) -> str:
    return f"{manifest.id}:{manifest.version}:{manifest.author}"


class CircularDependencyError(ValueError):
    pass


class PluginValidator:
    """The sprint's "VALIDATION" spec: compatibilité, permissions,
    signature, dépendances, conformité — run before a manifest can
    leave `DEVELOPMENT` (see `tmis.platform_sdk.publishing`). Reuses
    `tmis.platform.licensing.signing.LicenseKeySigner` (Sprint 10)
    for signing/verification rather than building a second HMAC
    scheme — the signer is already a generic opaque-payload signer,
    not license-specific."""

    def __init__(self, registry: PluginRegistryPort, signer: LicenseKeySigner) -> None:
        self._registry = registry
        self._signer = signer

    def validate(self, manifest: PluginManifest) -> ValidationReport:
        issues: list[ValidationIssue] = []
        issues.extend(self._check_conformity(manifest))
        issues.extend(self._check_permissions(manifest))
        issues.extend(self._check_compatibility(manifest))
        issues.extend(self._check_dependencies(manifest))
        if manifest.signature is not None:
            issues.extend(self._check_signature(manifest))
        return ValidationReport(plugin_id=manifest.id, issues=tuple(issues))

    def sign(self, manifest: PluginManifest) -> str:
        return self._signer.sign(_canonical_payload(manifest))

    def verify_signature(self, manifest: PluginManifest) -> bool:
        if manifest.signature is None:
            return False
        decoded = self._signer.verify(manifest.signature)
        return decoded == _canonical_payload(manifest)

    @staticmethod
    def _check_conformity(manifest: PluginManifest) -> list[ValidationIssue]:
        issues = []
        if not manifest.id:
            issues.append(ValidationIssue("id", "l'identifiant est obligatoire"))
        if not manifest.name:
            issues.append(ValidationIssue("name", "le nom est obligatoire"))
        if not manifest.version:
            issues.append(ValidationIssue("version", "la version est obligatoire"))
        if not manifest.license:
            issues.append(ValidationIssue("license", "la licence est obligatoire"))
        if not manifest.description:
            issues.append(ValidationIssue("description", "la description est obligatoire"))
        return issues

    @staticmethod
    def _check_permissions(manifest: PluginManifest) -> list[ValidationIssue]:
        issues = []
        for permission in manifest.permissions:
            try:
                ExtensionPermission(permission)
            except ValueError:
                issues.append(
                    ValidationIssue("permissions", f"permission inconnue : {permission!r}")
                )
        return issues

    @staticmethod
    def _check_compatibility(manifest: PluginManifest) -> list[ValidationIssue]:
        if manifest.compatibility in ("*", SDK_VERSION):
            return []
        return [
            ValidationIssue(
                "compatibility",
                f"incompatible avec le SDK {SDK_VERSION} "
                f"(déclaré : {manifest.compatibility!r})",
            )
        ]

    def _check_dependencies(self, manifest: PluginManifest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for dependency_id in manifest.dependencies:
            if dependency_id == manifest.id:
                issues.append(
                    ValidationIssue("dependencies", f"dépendance vers soi-même : {dependency_id}")
                )
                continue
            if self._registry.get(dependency_id) is None:
                issues.append(
                    ValidationIssue("dependencies", f"dépendance introuvable : {dependency_id}")
                )
                continue
            try:
                self._assert_no_cycle(manifest.id, dependency_id, visited={manifest.id})
            except CircularDependencyError as exc:
                issues.append(ValidationIssue("dependencies", str(exc)))
        return issues

    def _assert_no_cycle(self, root_id: str, current_id: str, visited: set[str]) -> None:
        if current_id in visited:
            raise CircularDependencyError(f"dépendance circulaire détectée sur {current_id}")
        manifest = self._registry.get(current_id)
        if manifest is None:
            return
        next_visited = visited | {current_id}
        for dependency_id in manifest.dependencies:
            if dependency_id == root_id:
                raise CircularDependencyError(f"dépendance circulaire détectée sur {root_id}")
            self._assert_no_cycle(root_id, dependency_id, next_visited)

    def _check_signature(self, manifest: PluginManifest) -> list[ValidationIssue]:
        if self.verify_signature(manifest):
            return []
        return [ValidationIssue("signature", "signature invalide ou altérée")]
