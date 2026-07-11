from tmis.ai_fabric.comparison.engine import ComparisonEngine
from tmis.ai_fabric.comparison.schemas import ComparisonResult
from tmis.ai_fabric.consensus.engine import ConsensusEngine
from tmis.ai_fabric.consensus.schemas import ConsensusOutcome, ModelPosition
from tmis.ai_fabric.critic.engine import CriticModel
from tmis.ai_fabric.critic.schemas import CriticVerdict
from tmis.ai_fabric.fusion.engine import FusionEngine
from tmis.ai_fabric.fusion.schemas import FusedResponse
from tmis.ai_fabric.planner.engine import TaskPlanner
from tmis.ai_fabric.planner.schemas import ExecutionPlan
from tmis.ai_fabric.router.engine import RouterEngine
from tmis.ai_fabric.router.schemas import RoutingDecision, RoutingRequest


class AIIntelligenceFabric:
    """The single entry point every business module (`case_intelligence`,
    `legal_drafting`, `legal_reasoning`, `cabinet_knowledge`, ...) is
    expected to go through for any model-related decision — per the
    sprint's constraints "toutes les interactions IA passent par
    l'AI Intelligence Fabric" and "aucun module métier ne connaît
    directement un fournisseur". Composes the router, planner, critic,
    comparison, consensus, and fusion engines behind one facade so a
    caller never needs to import `tmis.ai.providers` directly."""

    def __init__(
        self,
        router: RouterEngine,
        planner: TaskPlanner,
        critic: CriticModel,
        comparison: ComparisonEngine,
        consensus: ConsensusEngine,
        fusion: FusionEngine,
    ) -> None:
        self.router = router
        self.planner = planner
        self.critic = critic
        self.comparison = comparison
        self.consensus = consensus
        self.fusion = fusion

    def route(self, request: RoutingRequest) -> RoutingDecision:
        return self.router.route(request)

    def plan(self, firm_id: str, task_description: str) -> ExecutionPlan:
        return self.planner.plan(firm_id, task_description)

    def review(self, model_name: str, response_text: str) -> CriticVerdict:
        return self.critic.review(model_name, response_text)

    def compare(self, prompt: str, responses: dict[str, str]) -> ComparisonResult:
        return self.comparison.compare(prompt, responses)

    def build_consensus(self, topic: str, positions: list[ModelPosition]) -> ConsensusOutcome:
        return self.consensus.build_consensus(topic, positions)

    def fuse(self, positions: list[ModelPosition]) -> FusedResponse:
        return self.fusion.fuse(positions)
