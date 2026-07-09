import uuid
from typing import Protocol

from tmis.domain.firm.entities import Firm


class FirmRepositoryPort(Protocol):
    """Persistence port for the `firm` bounded context."""

    def get_by_id(self, firm_id: uuid.UUID) -> Firm | None: ...

    def add(self, firm: Firm) -> None: ...
