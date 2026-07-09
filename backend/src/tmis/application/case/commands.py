import uuid
from dataclasses import dataclass

from tmis.domain.case.entities import Case
from tmis.domain.case.ports import CaseRepositoryPort


@dataclass
class CreateCaseCommand:
    firm_id: uuid.UUID
    title: str


class CreateCaseUseCase:
    """Application service: create a new case (CQRS command side)."""

    def __init__(self, case_repository: CaseRepositoryPort) -> None:
        self._case_repository = case_repository

    def execute(self, command: CreateCaseCommand) -> Case:
        case = Case(id=uuid.uuid4(), firm_id=command.firm_id, title=command.title)
        self._case_repository.add(case)
        return case
