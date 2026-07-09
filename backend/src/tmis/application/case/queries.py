import uuid
from dataclasses import dataclass

from tmis.domain.case.entities import Case
from tmis.domain.case.ports import CaseRepositoryPort


@dataclass
class ListCasesQuery:
    firm_id: uuid.UUID


class ListCasesUseCase:
    """Application service: list cases for a firm (CQRS query side)."""

    def __init__(self, case_repository: CaseRepositoryPort) -> None:
        self._case_repository = case_repository

    def execute(self, query: ListCasesQuery) -> list[Case]:
        return self._case_repository.list_by_firm(query.firm_id)
