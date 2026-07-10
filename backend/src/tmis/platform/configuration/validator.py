from typing import Protocol

from tmis.platform.configuration.schemas import ConfigIssue, EnvironmentTier

_INSECURE_DEFAULT = "change-me-in-production"


class ConfigurableSettings(Protocol):
    """The subset of `tmis.core.config.Settings` the validator needs —
    a narrow Protocol so this module never imports the concrete
    Settings class (avoids a forward dependency from platform/ onto
    core/)."""

    environment: str
    debug: bool
    jwt_secret_key: str
    license_signing_key: str
    cors_allowed_origins: list[str]


def validate_production_readiness(settings: ConfigurableSettings) -> list[ConfigIssue]:
    """Twelve-Factor config validator: flags settings that are safe
    defaults for local development but must never reach production
    (see docs/47-guide-securite-entreprise.md — Configuration). Called
    at startup so a misconfigured production deployment fails loudly
    rather than silently running with insecure defaults."""

    if settings.environment != EnvironmentTier.PRODUCTION.value:
        return []

    issues: list[ConfigIssue] = []
    if settings.debug:
        issues.append(
            ConfigIssue(
                field="debug", severity="critical", message="debug mode must be off in production"
            )
        )
    if settings.jwt_secret_key == _INSECURE_DEFAULT:
        issues.append(
            ConfigIssue(
                field="jwt_secret_key",
                severity="critical",
                message="jwt_secret_key is still the insecure default",
            )
        )
    if settings.license_signing_key == _INSECURE_DEFAULT:
        issues.append(
            ConfigIssue(
                field="license_signing_key",
                severity="critical",
                message="license_signing_key is still the insecure default",
            )
        )
    if "*" in settings.cors_allowed_origins:
        issues.append(
            ConfigIssue(
                field="cors_allowed_origins",
                severity="high",
                message="wildcard CORS origin must not be used in production",
            )
        )
    return issues
