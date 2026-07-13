from tmis.cloud_operations.profiling.schemas import ProfilingFindingType, ProfilingSample


class InMemoryProfilingSampleStore:
    def __init__(self) -> None:
        self._samples: list[ProfilingSample] = []

    def save(self, sample: ProfilingSample) -> None:
        self._samples.append(sample)

    def list_for_finding_type(self, finding_type: ProfilingFindingType) -> list[ProfilingSample]:
        return [s for s in self._samples if s.finding_type is finding_type]
