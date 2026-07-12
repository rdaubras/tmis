from tmis.identity_platform.teams.schemas import Team


class InMemoryTeamStore:
    def __init__(self) -> None:
        self._teams: dict[str, Team] = {}

    def save(self, team: Team) -> None:
        self._teams[team.id] = team

    def get(self, firm_id: str, team_id: str) -> Team | None:
        team = self._teams.get(team_id)
        if team is None or team.firm_id != firm_id:
            return None
        return team

    def list_for_department(self, firm_id: str, department_id: str) -> list[Team]:
        return [
            t
            for t in self._teams.values()
            if t.firm_id == firm_id and t.department_id == department_id
        ]
