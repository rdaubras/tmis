from typing import Protocol

from tmis.identity_platform.teams.schemas import Team


class TeamStorePort(Protocol):
    def save(self, team: Team) -> None: ...

    def get(self, firm_id: str, team_id: str) -> Team | None: ...

    def list_for_department(self, firm_id: str, department_id: str) -> list[Team]: ...
