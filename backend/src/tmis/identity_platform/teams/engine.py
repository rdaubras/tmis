from tmis.identity_platform.teams.ports import TeamStorePort
from tmis.identity_platform.teams.schemas import Team, new_team_id


class TeamEngine:
    def __init__(self, store: TeamStorePort) -> None:
        self._store = store

    def create(self, firm_id: str, department_id: str, name: str) -> Team:
        team = Team(id=new_team_id(), firm_id=firm_id, department_id=department_id, name=name)
        self._store.save(team)
        return team

    def get(self, firm_id: str, team_id: str) -> Team:
        team = self._store.get(firm_id, team_id)
        if team is None:
            raise KeyError(team_id)
        return team

    def list_for_department(self, firm_id: str, department_id: str) -> list[Team]:
        return self._store.list_for_department(firm_id, department_id)
