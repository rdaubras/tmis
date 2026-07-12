from tmis.identity_platform.departments.schemas import Department


class InMemoryDepartmentStore:
    def __init__(self) -> None:
        self._departments: dict[str, Department] = {}

    def save(self, department: Department) -> None:
        self._departments[department.id] = department

    def get(self, firm_id: str, department_id: str) -> Department | None:
        department = self._departments.get(department_id)
        if department is None or department.firm_id != firm_id:
            return None
        return department

    def list_for_firm(self, firm_id: str) -> list[Department]:
        return [d for d in self._departments.values() if d.firm_id == firm_id]
