from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.reasoning_patterns.schemas import (
    ReasoningPattern,
    pattern_from_knowledge_object,
)
from tmis.legal_copilot_framework.reasoning_packs.ports import ReasoningPackStorePort
from tmis.legal_copilot_framework.reasoning_packs.schemas import (
    ReasoningPack,
    ReasoningStrategyType,
)


class ReasoningPackEngine:
    """Declares which `legal_reasoning` strategies a copilot uses and
    resolves the stored `cabinet_knowledge.reasoning_patterns.
    ReasoningPattern` knowledge artifacts that back them — never
    executes a strategy itself; execution stays entirely in
    `legal_reasoning`."""

    def __init__(self, store: ReasoningPackStorePort, knowledge_space: KnowledgeSpace) -> None:
        self._store = store
        self._knowledge_space = knowledge_space

    def register_pack(
        self,
        pack_id: str,
        name: str,
        domain: LegalDomain,
        strategy_types: frozenset[ReasoningStrategyType],
        *,
        pattern_ids: tuple[str, ...] = (),
    ) -> ReasoningPack:
        existing = self._store.history(pack_id)
        version = existing[-1].version + 1 if existing else 1
        pack = ReasoningPack(
            id=pack_id,
            name=name,
            domain=domain,
            version=version,
            strategy_types=strategy_types,
            pattern_ids=pattern_ids,
        )
        self._store.save(pack)
        return pack

    def get(self, pack_id: str, version: int | None = None) -> ReasoningPack:
        pack = self._store.get(pack_id, version)
        if pack is None:
            raise KeyError(pack_id)
        return pack

    def resolve_patterns(self, firm_id: str, pack_id: str) -> list[ReasoningPattern]:
        pack = self.get(pack_id)
        patterns = []
        for pattern_id in pack.pattern_ids:
            obj = self._knowledge_space.get(firm_id, pattern_id)
            if obj is not None:
                patterns.append(pattern_from_knowledge_object(obj))
        return patterns
