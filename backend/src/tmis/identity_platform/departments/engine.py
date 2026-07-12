from tmis.identity_platform.departments.ports import DepartmentStorePort
from tmis.identity_platform.departments.schemas import Department, new_department_id


class DepartmentEngine:
    def __init__(self, store: DepartmentStorePort) -> None:
        self._store = store

    def create(self, firm_id: str, name: str) -> Department:
        department = Department(id=new_department_id(), firm_id=firm_id, name=name)
        self._store.save(department)
        return department

    def get(self, firm_id: str, department_id: str) -> Department:
        department = self._store.get(firm_id, department_id)
        if department is None:
            raise KeyError(department_id)
        return department

    def list_for_firm(self, firm_id: str) -> list[Department]:
        return self._store.list_for_firm(firm_id)
