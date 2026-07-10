from dataclasses import dataclass, field

from tmis.platform.autoscaling.schemas import AutoscalingPolicy
from tmis.platform.deployment.schemas import DeploymentProfile


@dataclass(frozen=True, slots=True)
class KubernetesManifestConfig:
    """Everything needed to render the manifest set for one
    environment (see docs/47-guide-securite-entreprise.md —
    Kubernetes)."""

    namespace: str
    app_name: str
    image: str
    container_port: int
    profile: DeploymentProfile
    autoscaling: AutoscalingPolicy
    ingress_host: str
    tls_secret_name: str
    config_map_data: dict[str, str] = field(default_factory=dict)
    secret_keys: tuple[str, ...] = ()
