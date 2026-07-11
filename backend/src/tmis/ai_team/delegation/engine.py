from tmis.ai_team.delegation.schemas import DelegationRecord
from tmis.ai_team.planner.schemas import SubTask
from tmis.ai_team.registry.ports import AgentRegistryPort
from tmis.ai_team.teams.schemas import Team


class DelegationEngine:
    """Resolves each `SubTask.assigned_role` to a concrete agent id
    within a `Team`, and keeps an append-only record of every decision
    (see docs/55-guide-coordinateur.md — Delegation). Used by the
    Coordinator, never called directly by an agent."""

    def __init__(self, registry: AgentRegistryPort) -> None:
        self._registry = registry
        self._records: list[DelegationRecord] = []

    def assign_agent(self, mission_id: str, sub_task: SubTask, team: Team) -> str | None:
        team_descriptors = {
            descriptor.id: descriptor
            for agent_id in team.member_agent_ids
            if (descriptor := self._registry.get(agent_id)) is not None
        }
        matching = [
            agent_id
            for agent_id, descriptor in team_descriptors.items()
            if descriptor.role == sub_task.assigned_role
        ]
        agent_id = matching[0] if matching else None
        self._records.append(
            DelegationRecord(mission_id=mission_id, sub_task_id=sub_task.id, agent_id=agent_id)
        )
        return agent_id

    def records_for_mission(self, mission_id: str) -> list[DelegationRecord]:
        return [r for r in self._records if r.mission_id == mission_id]
