import uuid
from dataclasses import dataclass


def new_team_id() -> str:
    return f"team-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class Team:
    id: str
    firm_id: str
    department_id: str
    name: str
