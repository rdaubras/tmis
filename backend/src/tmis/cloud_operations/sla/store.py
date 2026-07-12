from tmis.cloud_operations.sla.schemas import SLAMetricType, SLASample, SLATarget


class InMemorySLATargetStore:
    def __init__(self) -> None:
        self._targets: dict[tuple[str, SLAMetricType], SLATarget] = {}

    def save(self, target: SLATarget) -> None:
        self._targets[(target.service_name, target.metric_type)] = target

    def get(self, service_name: str, metric_type: SLAMetricType) -> SLATarget | None:
        return self._targets.get((service_name, metric_type))

    def list_for_service(self, service_name: str) -> list[SLATarget]:
        return [t for (name, _), t in self._targets.items() if name == service_name]


class InMemorySLASampleStore:
    def __init__(self) -> None:
        self._samples: list[SLASample] = []

    def save(self, sample: SLASample) -> None:
        self._samples.append(sample)

    def list_for_metric(self, service_name: str, metric_type: SLAMetricType) -> list[SLASample]:
        return [
            s
            for s in self._samples
            if s.service_name == service_name and s.metric_type is metric_type
        ]
