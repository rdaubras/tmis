from typing import Protocol

from tmis.cloud_operations.sla.schemas import SLAMetricType
from tmis.cloud_operations.slo.schemas import SLOTarget


class SLOTargetStorePort(Protocol):
    def save(self, target: SLOTarget) -> None: ...

    def get(self, service_name: str, metric_type: SLAMetricType) -> SLOTarget | None: ...
