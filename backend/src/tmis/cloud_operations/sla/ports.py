from typing import Protocol

from tmis.cloud_operations.sla.schemas import SLAMetricType, SLASample, SLATarget


class SLATargetStorePort(Protocol):
    def save(self, target: SLATarget) -> None: ...

    def get(self, service_name: str, metric_type: SLAMetricType) -> SLATarget | None: ...

    def list_for_service(self, service_name: str) -> list[SLATarget]: ...


class SLASampleStorePort(Protocol):
    def save(self, sample: SLASample) -> None: ...

    def list_for_metric(self, service_name: str, metric_type: SLAMetricType) -> list[SLASample]: ...
