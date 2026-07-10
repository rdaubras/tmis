from tmis.platform.deployment.schemas import DeploymentProfile, DeploymentTier

_PRESETS: dict[DeploymentTier, DeploymentProfile] = {
    DeploymentTier.SOLO: DeploymentProfile(
        tier=DeploymentTier.SOLO,
        replicas=1,
        cpu_request="250m",
        cpu_limit="500m",
        memory_request="256Mi",
        memory_limit="512Mi",
        max_ai_concurrency=2,
    ),
    DeploymentTier.CABINET_SMALL: DeploymentProfile(
        tier=DeploymentTier.CABINET_SMALL,
        replicas=2,
        cpu_request="500m",
        cpu_limit="1",
        memory_request="512Mi",
        memory_limit="1Gi",
        max_ai_concurrency=5,
    ),
    DeploymentTier.CABINET_LARGE: DeploymentProfile(
        tier=DeploymentTier.CABINET_LARGE,
        replicas=4,
        cpu_request="1",
        cpu_limit="2",
        memory_request="1Gi",
        memory_limit="2Gi",
        max_ai_concurrency=15,
    ),
    DeploymentTier.ENTERPRISE: DeploymentProfile(
        tier=DeploymentTier.ENTERPRISE,
        replicas=8,
        cpu_request="2",
        cpu_limit="4",
        memory_request="2Gi",
        memory_limit="4Gi",
        max_ai_concurrency=40,
    ),
}


def profile_for_tier(tier: DeploymentTier) -> DeploymentProfile:
    return _PRESETS[tier]
