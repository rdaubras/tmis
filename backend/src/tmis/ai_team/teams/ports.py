from typing import Protocol

from tmis.ai_team.teams.schemas import Team


class TeamStorePort(Protocol):
    def save(self, team: Team) -> None: ...

    def get(self, team_id: str) -> Team | None: ...

    def list_all(self) -> list[Team]: ...
