from tmis.ai_team.coordinator.schemas import Mission


class InMemoryMissionStore:
    def __init__(self) -> None:
        self._missions: dict[str, Mission] = {}

    def save(self, mission: Mission) -> None:
        self._missions[mission.id] = mission

    def get(self, mission_id: str) -> Mission | None:
        return self._missions.get(mission_id)

    def list_for_firm(self, firm_id: str) -> list[Mission]:
        return [m for m in self._missions.values() if m.firm_id == firm_id]

    def list_all(self) -> list[Mission]:
        return list(self._missions.values())
