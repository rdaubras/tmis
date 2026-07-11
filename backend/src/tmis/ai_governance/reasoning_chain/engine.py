import uuid

from tmis.ai_governance.reasoning_chain.ports import ReasoningChainStorePort
from tmis.ai_governance.reasoning_chain.schemas import (
    ChainEdge,
    ChainNode,
    ChainStageType,
    ChainStep,
    OutOfOrderStepError,
    ReasoningChain,
    ReasoningChainGraph,
    new_chain_step_id,
)

_STAGE_ORDER: dict[ChainStageType, int] = {
    stage: index for index, stage in enumerate(ChainStageType)
}


class ReasoningChainEngine:
    """Extends `tmis.legal_reasoning`'s reasoning session with a
    governance-facing, cross-context chain: any production — not only
    a `legal_reasoning.ReasoningSession` — can record its progress
    through the sprint's eight canonical stages. Steps are append-only
    and must move forward through `ChainStageType`'s declared order,
    never backward, so the recorded chain always reads as a coherent
    story."""

    def __init__(self, store: ReasoningChainStorePort) -> None:
        self._store = store

    def get_or_create(self, firm_id: str, production_id: str) -> ReasoningChain:
        existing = self._store.get(firm_id, production_id)
        if existing is not None:
            return existing
        chain = ReasoningChain(id=str(uuid.uuid4()), firm_id=firm_id, production_id=production_id)
        self._store.save(chain)
        return chain

    def record_step(
        self,
        firm_id: str,
        production_id: str,
        stage: ChainStageType,
        summary: str,
        references: tuple[str, ...] = (),
    ) -> ChainStep:
        chain = self.get_or_create(firm_id, production_id)
        if chain.steps:
            last_stage = chain.steps[-1].stage
            if _STAGE_ORDER[stage] < _STAGE_ORDER[last_stage]:
                raise OutOfOrderStepError(last_stage, stage)
        step = ChainStep(
            id=new_chain_step_id(), stage=stage, summary=summary, references=references
        )
        chain.steps.append(step)
        self._store.save(chain)
        return step

    def chain_for(self, firm_id: str, production_id: str) -> ReasoningChain:
        return self.get_or_create(firm_id, production_id)

    def to_graph(self, firm_id: str, production_id: str) -> ReasoningChainGraph:
        chain = self.get_or_create(firm_id, production_id)
        nodes = tuple(
            ChainNode(id=step.id, stage=step.stage, label=step.summary) for step in chain.steps
        )
        edges = tuple(
            ChainEdge(source_id=chain.steps[i].id, target_id=chain.steps[i + 1].id)
            for i in range(len(chain.steps) - 1)
        )
        return ReasoningChainGraph(nodes=nodes, edges=edges)
