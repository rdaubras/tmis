from tmis.ai.embeddings.ports import EmbeddingProviderPort
from tmis.ai.embeddings.similarity import cosine_similarity
from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.schemas import ValidationRequest
from tmis.cabinet_knowledge.ontology.schemas import RelationType
from tmis.case_intelligence.actors.merger import normalize_name
from tmis.legal_knowledge_graph.entity_resolution.ports import ResolutionMatchStorePort
from tmis.legal_knowledge_graph.entity_resolution.schemas import (
    ResolutionMatch,
    ResolutionStatus,
    new_resolution_match_id,
)
from tmis.legal_knowledge_graph.graph_core.engine import GraphEngine

_AUTO_CONFIRM_THRESHOLD = 0.98
"""Only an exact normalized-name match (score 1.0, same patron as
`case_intelligence.actors.merger.normalize_name`) auto-confirms —
everything else always waits for a human decision, per the sprint's
own "aucune connaissance ne peut être ajoutée automatiquement sans
validation humaine" constraint (Sprint 12, still in force)."""


class EntityResolutionEngine:
    """Generalizes `case_intelligence.actors.ActorMerger`'s
    normalized-name matching (Sprint 4) — scoped to one case there,
    scoped to the whole firm's graph here — with scoring, human
    validation (via `ai_governance.human_validation`, Sprint 15) and
    a full history of every decision, none of which the original
    `ActorMerger` needed."""

    def __init__(
        self,
        store: ResolutionMatchStorePort,
        graph: GraphEngine,
        embedding_provider: EmbeddingProviderPort,
        human_validation: HumanValidationEngine,
    ) -> None:
        self._store = store
        self._graph = graph
        self._embedding_provider = embedding_provider
        self._human_validation = human_validation

    async def score(self, firm_id: str, node_id_a: str, node_id_b: str) -> float:
        node_a = self._graph.get_node(firm_id, node_id_a)
        node_b = self._graph.get_node(firm_id, node_id_b)
        if normalize_name(node_a.label) == normalize_name(node_b.label):
            return 1.0
        vectors = await self._embedding_provider.embed([node_a.label, node_b.label])
        return cosine_similarity(vectors[0], vectors[1])

    async def propose_match(self, firm_id: str, node_id_a: str, node_id_b: str) -> ResolutionMatch:
        score = await self.score(firm_id, node_id_a, node_id_b)
        status = (
            ResolutionStatus.CONFIRMED
            if score >= _AUTO_CONFIRM_THRESHOLD
            else ResolutionStatus.PENDING
        )
        match = ResolutionMatch(
            id=new_resolution_match_id(),
            firm_id=firm_id,
            node_id_a=node_id_a,
            node_id_b=node_id_b,
            score=score,
            status=status,
        )
        self._store.save(match)
        if status is ResolutionStatus.CONFIRMED:
            self._link_as_same(firm_id, match, "correspondance automatique (nom identique)")
        return match

    def get(self, firm_id: str, match_id: str) -> ResolutionMatch:
        match = self._store.get_latest(firm_id, match_id)
        if match is None:
            raise KeyError(match_id)
        return match

    def history(self, firm_id: str, match_id: str) -> list[ResolutionMatch]:
        return self._store.history(firm_id, match_id)

    def request_human_review(
        self, firm_id: str, match_id: str, requested_by: str, approver_ids: tuple[str, ...]
    ) -> ValidationRequest:
        self.get(firm_id, match_id)
        return self._human_validation.request_simple(firm_id, match_id, requested_by, approver_ids)

    def confirm(self, firm_id: str, match_id: str, actor: str) -> ResolutionMatch:
        match = self.get(firm_id, match_id)
        confirmed = ResolutionMatch(
            id=match.id,
            firm_id=match.firm_id,
            node_id_a=match.node_id_a,
            node_id_b=match.node_id_b,
            score=match.score,
            status=ResolutionStatus.CONFIRMED,
            decided_by=actor,
        )
        self._store.save(confirmed)
        self._link_as_same(firm_id, confirmed, f"confirmé par {actor}")
        return confirmed

    def reject(self, firm_id: str, match_id: str, actor: str) -> ResolutionMatch:
        match = self.get(firm_id, match_id)
        rejected = ResolutionMatch(
            id=match.id,
            firm_id=match.firm_id,
            node_id_a=match.node_id_a,
            node_id_b=match.node_id_b,
            score=match.score,
            status=ResolutionStatus.REJECTED,
            decided_by=actor,
        )
        self._store.save(rejected)
        return rejected

    def _link_as_same(self, firm_id: str, match: ResolutionMatch, explanation: str) -> None:
        self._graph.link(
            firm_id,
            match.node_id_a,
            match.node_id_b,
            RelationType.SAME_AS,
            explanation=explanation,
            confidence=match.score,
        )
