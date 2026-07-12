from tmis.cloud_operations.sla.ports import SLASampleStorePort, SLATargetStorePort
from tmis.cloud_operations.sla.schemas import (
    _LOWER_IS_BETTER,
    SLAIndicator,
    SLAMetricType,
    SLASample,
    SLATarget,
    new_sla_sample_id,
    new_sla_target_id,
)


class SLAEngine:
    """Tracks the four SLA indicators the sprint asks for
    ("disponibilité, latence, taux de réussite, temps de
    restauration") against configurable targets, computing each
    indicator automatically from historized samples — never a manual
    calculation."""

    def __init__(self, targets: SLATargetStorePort, samples: SLASampleStorePort) -> None:
        self._targets = targets
        self._samples = samples

    def set_target(
        self, service_name: str, metric_type: SLAMetricType, target_value: float
    ) -> SLATarget:
        target = SLATarget(
            id=new_sla_target_id(),
            service_name=service_name,
            metric_type=metric_type,
            target_value=target_value,
        )
        self._targets.save(target)
        return target

    def record_sample(
        self, service_name: str, metric_type: SLAMetricType, value: float
    ) -> SLASample:
        sample = SLASample(
            id=new_sla_sample_id(),
            service_name=service_name,
            metric_type=metric_type,
            value=value,
        )
        self._samples.save(sample)
        return sample

    def average_value(self, service_name: str, metric_type: SLAMetricType) -> float | None:
        samples = self._samples.list_for_metric(service_name, metric_type)
        if not samples:
            return None
        return sum(s.value for s in samples) / len(samples)

    def compute_indicator(
        self, service_name: str, metric_type: SLAMetricType
    ) -> SLAIndicator | None:
        target = self._targets.get(service_name, metric_type)
        actual = self.average_value(service_name, metric_type)
        if target is None or actual is None:
            return None
        if metric_type in _LOWER_IS_BETTER:
            met = actual <= target.target_value
        else:
            met = actual >= target.target_value
        return SLAIndicator(
            service_name=service_name,
            metric_type=metric_type,
            target_value=target.target_value,
            actual_value=actual,
            met=met,
        )

    def indicators_for_service(self, service_name: str) -> list[SLAIndicator]:
        indicators = []
        for target in self._targets.list_for_service(service_name):
            indicator = self.compute_indicator(service_name, target.metric_type)
            if indicator is not None:
                indicators.append(indicator)
        return indicators
