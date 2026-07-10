from tmis.platform.autoscaling.schemas import AutoscalingPolicy
from tmis.platform.deployment.schemas import DeploymentTier

_PRESETS: dict[DeploymentTier, AutoscalingPolicy] = {
    DeploymentTier.SOLO: AutoscalingPolicy(
        min_replicas=1, max_replicas=2, target_cpu_percent=75, target_memory_percent=80
    ),
    DeploymentTier.CABINET_SMALL: AutoscalingPolicy(
        min_replicas=2, max_replicas=4, target_cpu_percent=70, target_memory_percent=75
    ),
    DeploymentTier.CABINET_LARGE: AutoscalingPolicy(
        min_replicas=4, max_replicas=10, target_cpu_percent=65, target_memory_percent=75
    ),
    DeploymentTier.ENTERPRISE: AutoscalingPolicy(
        min_replicas=8, max_replicas=30, target_cpu_percent=60, target_memory_percent=70
    ),
}


def policy_for_tier(tier: DeploymentTier) -> AutoscalingPolicy:
    return _PRESETS[tier]
