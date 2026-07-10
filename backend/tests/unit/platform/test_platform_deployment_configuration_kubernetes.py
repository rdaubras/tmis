from dataclasses import dataclass

import pytest
import yaml

from tmis.platform.autoscaling.presets import policy_for_tier as autoscaling_for_tier
from tmis.platform.autoscaling.schemas import AutoscalingPolicy
from tmis.platform.configuration.schemas import ConfigIssue
from tmis.platform.configuration.validator import validate_production_readiness
from tmis.platform.deployment.presets import profile_for_tier
from tmis.platform.deployment.schemas import DeploymentTier
from tmis.platform.kubernetes.render import render_all, render_manifest_yaml
from tmis.platform.kubernetes.schemas import KubernetesManifestConfig


@dataclass
class _FakeSettings:
    environment: str
    debug: bool = False
    jwt_secret_key: str = "a-real-production-secret"
    license_signing_key: str = "another-real-production-secret"
    cors_allowed_origins: list[str] | None = None

    def __post_init__(self) -> None:
        if self.cors_allowed_origins is None:
            self.cors_allowed_origins = ["https://app.tmis.example.com"]


def test_validator_is_silent_outside_production() -> None:
    settings = _FakeSettings(environment="development", jwt_secret_key="change-me-in-production")

    assert validate_production_readiness(settings) == []


def test_validator_flags_every_insecure_default_in_production() -> None:
    settings = _FakeSettings(
        environment="production",
        debug=True,
        jwt_secret_key="change-me-in-production",
        license_signing_key="change-me-in-production",
        cors_allowed_origins=["*"],
    )

    issues = validate_production_readiness(settings)
    fields = {issue.field for issue in issues}

    assert fields == {"debug", "jwt_secret_key", "license_signing_key", "cors_allowed_origins"}
    assert all(isinstance(issue, ConfigIssue) for issue in issues)


def test_validator_passes_a_properly_configured_production_environment() -> None:
    settings = _FakeSettings(environment="production")

    assert validate_production_readiness(settings) == []


@pytest.mark.parametrize(
    "tier",
    [
        DeploymentTier.SOLO,
        DeploymentTier.CABINET_SMALL,
        DeploymentTier.CABINET_LARGE,
        DeploymentTier.ENTERPRISE,
    ],
)
def test_every_deployment_tier_has_a_valid_profile_and_autoscaling_policy(
    tier: DeploymentTier,
) -> None:
    profile = profile_for_tier(tier)
    policy = autoscaling_for_tier(tier)

    assert profile.tier is tier
    assert policy.min_replicas <= policy.max_replicas


def test_larger_tiers_scale_up_replicas_and_concurrency() -> None:
    solo = profile_for_tier(DeploymentTier.SOLO)
    enterprise = profile_for_tier(DeploymentTier.ENTERPRISE)

    assert enterprise.replicas > solo.replicas
    assert enterprise.max_ai_concurrency > solo.max_ai_concurrency


def test_autoscaling_policy_rejects_min_greater_than_max() -> None:
    with pytest.raises(ValueError):
        AutoscalingPolicy(
            min_replicas=5, max_replicas=2, target_cpu_percent=70, target_memory_percent=70
        )


def _manifest_config() -> KubernetesManifestConfig:
    return KubernetesManifestConfig(
        namespace="tmis-test",
        app_name="tmis-backend",
        image="ghcr.io/example/tmis-backend:latest",
        container_port=8000,
        profile=profile_for_tier(DeploymentTier.CABINET_SMALL),
        autoscaling=autoscaling_for_tier(DeploymentTier.CABINET_SMALL),
        ingress_host="pilot.tmis.example.com",
        tls_secret_name="tmis-tls",
        config_map_data={"TMIS_ENVIRONMENT": "production"},
        secret_keys=("TMIS_JWT_SECRET_KEY",),
    )


def test_render_all_produces_every_expected_manifest_kind() -> None:
    manifests = render_all(_manifest_config())

    assert set(manifests) == {
        "deployment.yaml",
        "service.yaml",
        "ingress.yaml",
        "configmap.yaml",
        "secret.yaml",
        "hpa.yaml",
        "networkpolicy.yaml",
        "poddisruptionbudget.yaml",
    }
    for text in manifests.values():
        parsed = yaml.safe_load(text)
        assert "kind" in parsed
        assert parsed["metadata"]["namespace"] == "tmis-test"


def test_deployment_manifest_wires_readiness_and_liveness_probes() -> None:
    text = render_manifest_yaml(_manifest_config(), "deployment")
    parsed = yaml.safe_load(text)

    container = parsed["spec"]["template"]["spec"]["containers"][0]
    assert container["readinessProbe"]["httpGet"]["path"] == "/platform/health/ready"
    assert container["livenessProbe"]["httpGet"]["path"] == "/platform/health/live"
    assert parsed["spec"]["replicas"] == profile_for_tier(DeploymentTier.CABINET_SMALL).replicas


def test_secret_manifest_never_contains_a_real_value() -> None:
    text = render_manifest_yaml(_manifest_config(), "secret")
    parsed = yaml.safe_load(text)

    assert parsed["stringData"]["TMIS_JWT_SECRET_KEY"] == "REPLACE_ME"


def test_hpa_manifest_reflects_the_autoscaling_policy() -> None:
    config = _manifest_config()
    text = render_manifest_yaml(config, "hpa")
    parsed = yaml.safe_load(text)

    assert parsed["spec"]["minReplicas"] == config.autoscaling.min_replicas
    assert parsed["spec"]["maxReplicas"] == config.autoscaling.max_replicas


def test_render_manifest_yaml_rejects_an_unknown_kind() -> None:
    with pytest.raises(ValueError, match="unknown manifest kind"):
        render_manifest_yaml(_manifest_config(), "not-a-real-kind")
