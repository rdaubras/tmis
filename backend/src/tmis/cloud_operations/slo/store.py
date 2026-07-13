from tmis.cloud_operations.sla.schemas import SLAMetricType
from tmis.cloud_operations.slo.schemas import SLOTarget


class InMemorySLOTargetStore:
    def __init__(self) -> None:
        self._targets: dict[tuple[str, SLAMetricType], SLOTarget] = {}

    def save(self, target: SLOTarget) -> None:
        self._targets[(target.service_name, target.metric_type)] = target

    def get(self, service_name: str, metric_type: SLAMetricType) -> SLOTarget | None:
        return self._targets.get((service_name, metric_type))
