from tmis.ai_team.teams.schemas import Team


class InMemoryTeamStore:
    def __init__(self) -> None:
        self._teams: dict[str, Team] = {}

    def save(self, team: Team) -> None:
        self._teams[team.id] = team

    def get(self, team_id: str) -> Team | None:
        return self._teams.get(team_id)

    def list_all(self) -> list[Team]:
        return list(self._teams.values())
