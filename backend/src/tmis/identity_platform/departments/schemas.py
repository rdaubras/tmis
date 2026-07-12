import uuid
from dataclasses import dataclass


def new_department_id() -> str:
    return f"dept-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class Department:
    id: str
    firm_id: str
    name: str
