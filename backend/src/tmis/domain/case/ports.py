import uuid
from typing import Protocol

from tmis.domain.case.entities import Case


class CaseRepositoryPort(Protocol):
    """Persistence port for the `case` bounded context."""

    def get_by_id(self, case_id: uuid.UUID, firm_id: uuid.UUID) -> Case | None: ...

    def list_by_firm(self, firm_id: uuid.UUID) -> list[Case]: ...

    def add(self, case: Case) -> None: ...
