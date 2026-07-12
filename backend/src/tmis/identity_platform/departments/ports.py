from typing import Protocol

from tmis.identity_platform.departments.schemas import Department


class DepartmentStorePort(Protocol):
    def save(self, department: Department) -> None: ...

    def get(self, firm_id: str, department_id: str) -> Department | None: ...

    def list_for_firm(self, firm_id: str) -> list[Department]: ...
