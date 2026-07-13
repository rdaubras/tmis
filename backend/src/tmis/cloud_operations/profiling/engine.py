from tmis.cloud_operations.profiling.ports import ProfilingSampleStorePort
from tmis.cloud_operations.profiling.schemas import (
    _RECOMMENDATION_TEMPLATES,
    ProfilingFindingType,
    ProfilingRecommendation,
    ProfilingSample,
    new_profiling_sample_id,
)


class ProfilingEngine:
    """Performance profiling — records timed samples for the four
    offender categories the sprint asks for (slow functions, costly
    queries, excessive AI calls, blocking operations) and surfaces
    the worst offenders with an optimization recommendation."""

    def __init__(self, store: ProfilingSampleStorePort) -> None:
        self._store = store

    def record(
        self,
        finding_type: ProfilingFindingType,
        name: str,
        duration_ms: float,
        firm_id: str | None = None,
    ) -> ProfilingSample:
        sample = ProfilingSample(
            id=new_profiling_sample_id(),
            finding_type=finding_type,
            name=name,
            duration_ms=duration_ms,
            firm_id=firm_id,
        )
        self._store.save(sample)
        return sample

    def top_offenders(
        self, finding_type: ProfilingFindingType, limit: int = 5
    ) -> list[ProfilingRecommendation]:
        samples = self._store.list_for_finding_type(finding_type)
        by_name: dict[str, list[float]] = {}
        for sample in samples:
            by_name.setdefault(sample.name, []).append(sample.duration_ms)

        recommendations = [
            ProfilingRecommendation(
                finding_type=finding_type,
                name=name,
                average_duration_ms=sum(durations) / len(durations),
                occurrence_count=len(durations),
                recommendation=_RECOMMENDATION_TEMPLATES[finding_type].format(
                    name=name, avg=sum(durations) / len(durations)
                ),
            )
            for name, durations in by_name.items()
        ]
        recommendations.sort(key=lambda r: r.average_duration_ms, reverse=True)
        return recommendations[:limit]
