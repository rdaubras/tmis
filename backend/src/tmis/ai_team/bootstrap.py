from functools import lru_cache

from tmis.ai_team.agents.bootstrap import get_default_agents
from tmis.ai_team.consensus.engine import ConsensusEngine
from tmis.ai_team.context.engine import ContextEngine
from tmis.ai_team.coordinator.engine import CoordinatorEngine
from tmis.ai_team.coordinator.store import InMemoryMissionStore
from tmis.ai_team.critique.engine import CritiqueEngine
from tmis.ai_team.delegation.engine import DelegationEngine
from tmis.ai_team.evaluation.engine import Evaluator
from tmis.ai_team.human_loop.engine import HumanLoopEngine
from tmis.ai_team.human_loop.store import InMemoryHumanDecisionStore
from tmis.ai_team.marketplace.store import InMemoryMarketplaceCatalog
from tmis.ai_team.memory.store import InMemoryAgentMemoryStore
from tmis.ai_team.metrics.engine import MetricsCollector
from tmis.ai_team.negotiation.engine import NegotiationEngine
from tmis.ai_team.planner.engine import Planner
from tmis.ai_team.registry.bootstrap import get_agent_registry
from tmis.ai_team.review.engine import ReviewEngine
from tmis.ai_team.teams.engine import TeamBuilder
from tmis.ai_team.teams.store import InMemoryTeamStore
from tmis.ai_team.work_queue.engine import InMemoryWorkQueue


@lru_cache
def get_work_queue() -> InMemoryWorkQueue:
    return InMemoryWorkQueue()


@lru_cache
def get_mission_store() -> InMemoryMissionStore:
    return InMemoryMissionStore()


@lru_cache
def get_team_store() -> InMemoryTeamStore:
    return InMemoryTeamStore()


@lru_cache
def get_human_decision_store() -> InMemoryHumanDecisionStore:
    return InMemoryHumanDecisionStore()


@lru_cache
def get_agent_memory_store() -> InMemoryAgentMemoryStore:
    return InMemoryAgentMemoryStore()


@lru_cache
def get_marketplace_catalog() -> InMemoryMarketplaceCatalog:
    return InMemoryMarketplaceCatalog()


@lru_cache
def get_metrics_collector() -> MetricsCollector:
    return MetricsCollector()


@lru_cache
def get_context_engine() -> ContextEngine:
    return ContextEngine()


@lru_cache
def get_planner() -> Planner:
    return Planner()


@lru_cache
def get_delegation_engine() -> DelegationEngine:
    return DelegationEngine(get_agent_registry())


@lru_cache
def get_team_builder() -> TeamBuilder:
    return TeamBuilder(get_agent_registry(), get_team_store())


@lru_cache
def get_consensus_engine() -> ConsensusEngine:
    return ConsensusEngine()


@lru_cache
def get_negotiation_engine() -> NegotiationEngine:
    return NegotiationEngine(get_consensus_engine())


@lru_cache
def get_critique_engine() -> CritiqueEngine:
    return CritiqueEngine()


@lru_cache
def get_review_engine() -> ReviewEngine:
    return ReviewEngine(get_critique_engine())


@lru_cache
def get_human_loop_engine() -> HumanLoopEngine:
    return HumanLoopEngine(get_human_decision_store())


@lru_cache
def get_evaluator() -> Evaluator:
    return Evaluator()


@lru_cache
def get_coordinator_engine() -> CoordinatorEngine:
    """Process-wide `CoordinatorEngine` singleton — the AI Team
    Platform's composition root (see docs/55-guide-coordinateur.md)."""
    return CoordinatorEngine(
        get_planner(),
        get_delegation_engine(),
        get_work_queue(),
        get_context_engine(),
        get_mission_store(),
        get_default_agents(),
        get_agent_registry(),
        get_metrics_collector(),
    )
