from typing import Protocol

from tmis.business_platform.metering.schemas import MeteredDimension, MeteringEvent


class MeteringEventStorePort(Protocol):
    def save(self, event: MeteringEvent) -> None: ...

    def list_for_firm(
        self, firm_id: str, dimension: MeteredDimension | None = None
    ) -> list[MeteringEvent]: ...
