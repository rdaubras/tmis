from typing import Any

from tmis.platform.kubernetes.schemas import KubernetesManifestConfig


def _labels(config: KubernetesManifestConfig) -> dict[str, str]:
    return {"app": config.app_name, "part-of": "tmis"}


def build_deployment(config: KubernetesManifestConfig) -> dict[str, Any]:
    labels = _labels(config)
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": config.app_name, "namespace": config.namespace, "labels": labels},
        "spec": {
            "replicas": config.profile.replicas,
            "selector": {"matchLabels": labels},
            "template": {
                "metadata": {"labels": labels},
                "spec": {
                    "containers": [
                        {
                            "name": config.app_name,
                            "image": config.image,
                            "ports": [{"containerPort": config.container_port}],
                            "envFrom": [
                                {"configMapRef": {"name": f"{config.app_name}-config"}},
                                {"secretRef": {"name": f"{config.app_name}-secrets"}},
                            ],
                            "resources": {
                                "requests": {
                                    "cpu": config.profile.cpu_request,
                                    "memory": config.profile.memory_request,
                                },
                                "limits": {
                                    "cpu": config.profile.cpu_limit,
                                    "memory": config.profile.memory_limit,
                                },
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": "/platform/health/ready",
                                    "port": config.container_port,
                                },
                                "periodSeconds": 10,
                            },
                            "livenessProbe": {
                                "httpGet": {
                                    "path": "/platform/health/live",
                                    "port": config.container_port,
                                },
                                "periodSeconds": 20,
                            },
                        }
                    ]
                },
            },
        },
    }


def build_service(config: KubernetesManifestConfig) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": config.app_name, "namespace": config.namespace},
        "spec": {
            "selector": _labels(config),
            "ports": [{"port": 80, "targetPort": config.container_port}],
        },
    }


def build_ingress(config: KubernetesManifestConfig) -> dict[str, Any]:
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": config.app_name,
            "namespace": config.namespace,
            "annotations": {"cert-manager.io/cluster-issuer": "letsencrypt"},
        },
        "spec": {
            "tls": [{"hosts": [config.ingress_host], "secretName": config.tls_secret_name}],
            "rules": [
                {
                    "host": config.ingress_host,
                    "http": {
                        "paths": [
                            {
                                "path": "/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": config.app_name,
                                        "port": {"number": 80},
                                    }
                                },
                            }
                        ]
                    },
                }
            ],
        },
    }


def build_config_map(config: KubernetesManifestConfig) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {"name": f"{config.app_name}-config", "namespace": config.namespace},
        "data": dict(config.config_map_data),
    }


def build_secret(config: KubernetesManifestConfig) -> dict[str, Any]:
    """Structural placeholder only — real values must be injected by a
    secret manager (Vault, Sealed Secrets, SOPS) at deploy time, never
    committed to this manifest."""
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": f"{config.app_name}-secrets", "namespace": config.namespace},
        "type": "Opaque",
        "stringData": {key: "REPLACE_ME" for key in config.secret_keys},
    }


def build_hpa(config: KubernetesManifestConfig) -> dict[str, Any]:
    policy = config.autoscaling
    return {
        "apiVersion": "autoscaling/v2",
        "kind": "HorizontalPodAutoscaler",
        "metadata": {"name": config.app_name, "namespace": config.namespace},
        "spec": {
            "scaleTargetRef": {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "name": config.app_name,
            },
            "minReplicas": policy.min_replicas,
            "maxReplicas": policy.max_replicas,
            "metrics": [
                {
                    "type": "Resource",
                    "resource": {
                        "name": "cpu",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": policy.target_cpu_percent,
                        },
                    },
                },
                {
                    "type": "Resource",
                    "resource": {
                        "name": "memory",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": policy.target_memory_percent,
                        },
                    },
                },
            ],
        },
    }


def build_network_policy(config: KubernetesManifestConfig) -> dict[str, Any]:
    """Default-deny ingress except from the ingress controller and
    same-namespace pods — enforces network-level tenant/service
    isolation as defense-in-depth alongside application-level
    multi-tenant checks."""
    labels = _labels(config)
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"name": f"{config.app_name}-default-deny", "namespace": config.namespace},
        "spec": {
            "podSelector": {"matchLabels": labels},
            "policyTypes": ["Ingress"],
            "ingress": [
                {
                    "from": [
                        {"namespaceSelector": {}},
                        {"podSelector": {"matchLabels": {"app": "ingress-nginx"}}},
                    ]
                }
            ],
        },
    }


def build_pod_disruption_budget(config: KubernetesManifestConfig) -> dict[str, Any]:
    return {
        "apiVersion": "policy/v1",
        "kind": "PodDisruptionBudget",
        "metadata": {"name": config.app_name, "namespace": config.namespace},
        "spec": {"minAvailable": "50%", "selector": {"matchLabels": _labels(config)}},
    }
