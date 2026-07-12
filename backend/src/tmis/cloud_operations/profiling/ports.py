from typing import Protocol

from tmis.cloud_operations.profiling.schemas import ProfilingFindingType, ProfilingSample


class ProfilingSampleStorePort(Protocol):
    def save(self, sample: ProfilingSample) -> None: ...

    def list_for_finding_type(
        self, finding_type: ProfilingFindingType
    ) -> list[ProfilingSample]: ...
