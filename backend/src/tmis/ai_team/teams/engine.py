import uuid

from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.capabilities.catalog import domain_expert_role
from tmis.ai_team.capabilities.mission_templates import (
    DEFAULT_MISSION_TEMPLATE,
    roles_for_case_type,
)
from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.ai_team.registry.ports import AgentRegistryPort
from tmis.ai_team.teams.ports import TeamStorePort
from tmis.ai_team.teams.schemas import MissionComplexity, Team


class TeamBuilder:
    """Composes a `Team` automatically from mission parameters, or lets
    a caller assemble a fully custom one (see
    docs/54-guide-creation-equipe.md). The role composition for each
    predefined case type comes from
    `tmis.ai_team.capabilities.mission_templates` — the same source
    `Planner` reads to build sub-tasks, so a team is never missing an
    agent a generated plan actually needs. The domain expert (RGPD/
    fiscal/social) is added on top of a template only when the
    mission's `LegalDomain` calls for it — "si pertinent", per the
    sprint brief."""

    def __init__(self, registry: AgentRegistryPort, store: TeamStorePort) -> None:
        self._registry = registry
        self._store = store

    def _resolve_role(self, role: AgentRole) -> str | None:
        candidates = self._registry.list_by_role(role)
        return candidates[0].id if candidates else None

    def build_team(
        self,
        domain: LegalDomain = LegalDomain.GENERAL,
        complexity: MissionComplexity = MissionComplexity.MEDIUM,
        case_type: str = DEFAULT_MISSION_TEMPLATE,
        target_cost_usd: float | None = None,
        desired_delay_seconds: float | None = None,
    ) -> Team:
        template_roles = list(roles_for_case_type(case_type))

        expert_role = domain_expert_role(domain)
        if expert_role is not None and complexity is not MissionComplexity.LOW:
            template_roles.append(expert_role)

        agent_ids = [aid for aid in (self._resolve_role(role) for role in template_roles) if aid]
        agent_ids = self._apply_budget(agent_ids, target_cost_usd, desired_delay_seconds)

        team = Team(
            id=str(uuid.uuid4()),
            name=f"Équipe {case_type} ({domain.value})",
            member_agent_ids=agent_ids,
            domain=domain,
        )
        self._store.save(team)
        return team

    def build_custom_team(self, name: str, agent_ids: list[str]) -> Team:
        team = Team(id=str(uuid.uuid4()), name=name, member_agent_ids=agent_ids, is_custom=True)
        self._store.save(team)
        return team

    def _apply_budget(
        self,
        agent_ids: list[str],
        target_cost_usd: float | None,
        desired_delay_seconds: float | None,
    ) -> list[str]:
        """Greedily keeps agents in template order until the running
        cost/time total would exceed the target — always keeps at
        least the first agent so a team is never empty."""
        if target_cost_usd is None and desired_delay_seconds is None:
            return agent_ids

        kept: list[str] = []
        total_cost = 0.0
        total_time = 0.0
        for agent_id in agent_ids:
            descriptor = self._registry.get(agent_id)
            if descriptor is None:
                continue
            next_cost = total_cost + descriptor.estimated_cost_usd
            next_time = total_time + descriptor.average_duration_seconds
            over_budget = target_cost_usd is not None and next_cost > target_cost_usd
            over_delay = desired_delay_seconds is not None and next_time > desired_delay_seconds
            if kept and (over_budget or over_delay):
                continue
            kept.append(agent_id)
            total_cost, total_time = next_cost, next_time
        return kept
