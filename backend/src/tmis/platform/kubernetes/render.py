import yaml

from tmis.platform.kubernetes.manifests import (
    build_config_map,
    build_deployment,
    build_hpa,
    build_ingress,
    build_network_policy,
    build_pod_disruption_budget,
    build_secret,
    build_service,
)
from tmis.platform.kubernetes.schemas import KubernetesManifestConfig

_BUILDERS = {
    "deployment": build_deployment,
    "service": build_service,
    "ingress": build_ingress,
    "configmap": build_config_map,
    "secret": build_secret,
    "hpa": build_hpa,
    "networkpolicy": build_network_policy,
    "poddisruptionbudget": build_pod_disruption_budget,
}


def render_manifest_yaml(config: KubernetesManifestConfig, kind: str) -> str:
    builder = _BUILDERS.get(kind)
    if builder is None:
        raise ValueError(f"unknown manifest kind: {kind}")
    return str(yaml.safe_dump(builder(config), sort_keys=False))


def render_all(config: KubernetesManifestConfig) -> dict[str, str]:
    """Renders every resource kind, keyed by a `<kind>.yaml` filename
    suitable for `kubectl apply -f`."""
    return {f"{kind}.yaml": render_manifest_yaml(config, kind) for kind in _BUILDERS}
