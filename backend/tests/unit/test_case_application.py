import uuid

from tmis.application.case.commands import CreateCaseCommand, CreateCaseUseCase
from tmis.application.case.queries import ListCasesQuery, ListCasesUseCase
from tmis.domain.case.entities import Case, CaseStatus


class InMemoryCaseRepository:
    def __init__(self) -> None:
        self.cases: dict[uuid.UUID, Case] = {}

    def get_by_id(self, case_id: uuid.UUID, firm_id: uuid.UUID) -> Case | None:
        case = self.cases.get(case_id)
        return case if case and case.firm_id == firm_id else None

    def list_by_firm(self, firm_id: uuid.UUID) -> list[Case]:
        return [c for c in self.cases.values() if c.firm_id == firm_id]

    def add(self, case: Case) -> None:
        self.cases[case.id] = case


def test_create_case_persists_via_repository() -> None:
    repo = InMemoryCaseRepository()
    firm_id = uuid.uuid4()
    use_case = CreateCaseUseCase(repo)

    case = use_case.execute(CreateCaseCommand(firm_id=firm_id, title="Dupont c. Durand"))

    assert case.status == CaseStatus.OPEN
    assert repo.get_by_id(case.id, firm_id) == case


def test_list_cases_only_returns_cases_of_requested_firm() -> None:
    repo = InMemoryCaseRepository()
    firm_a, firm_b = uuid.uuid4(), uuid.uuid4()
    CreateCaseUseCase(repo).execute(CreateCaseCommand(firm_id=firm_a, title="Dossier A"))
    CreateCaseUseCase(repo).execute(CreateCaseCommand(firm_id=firm_b, title="Dossier B"))

    result = ListCasesUseCase(repo).execute(ListCasesQuery(firm_id=firm_a))

    assert len(result) == 1
    assert result[0].title == "Dossier A"
