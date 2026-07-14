from collections.abc import Sequence

from tmis.knowledge_graph.entity_resolution.engine import EntityResolutionEngine
from tmis.knowledge_graph.entity_resolution.schemas import ResolvedEntity
from tmis.knowledge_graph.federation.engine import FederationQueryEngine
from tmis.knowledge_graph.federation.schemas import FederatedNeighborhood, GraphOrigin
from tmis.legal_copilot_framework.knowledge_packs.engine import KnowledgePackEngine
from tmis.legal_copilot_framework.knowledge_packs.schemas import KnowledgePack


def federated_relation_ref(origin: GraphOrigin, node_id: str) -> str:
    return f"{origin.value}:{node_id}"


def _parse_ref(ref: str) -> tuple[GraphOrigin, str]:
    origin_value, node_id = ref.split(":", 1)
    return GraphOrigin(origin_value), node_id


class CopilotKnowledgeBridge:
    """Lets a Knowledge Pack reference resolved entities and federated
    relations, composing `KnowledgePackEngine`, `EntityResolutionEngine`,
    and `FederationQueryEngine` — the pack itself only stores ids, this
    class resolves them fresh on every call, the same "pointer, not
    payload" pattern every other Pack in `legal_copilot_framework`
    follows.
    """

    def __init__(
        self,
        knowledge_pack_engine: KnowledgePackEngine,
        entity_resolution: EntityResolutionEngine,
        federation: FederationQueryEngine,
    ) -> None:
        self._knowledge_pack_engine = knowledge_pack_engine
        self._entity_resolution = entity_resolution
        self._federation = federation

    def attach_resolved_entities(
        self, firm_id: str, pack_id: str, entity_ids: Sequence[str]
    ) -> KnowledgePack:
        pack = self._knowledge_pack_engine.get(pack_id)
        valid_ids = {
            entity_id
            for entity_id in entity_ids
            if self._entity_resolution.get(firm_id, entity_id) is not None
        }
        merged_ids = tuple(dict.fromkeys((*pack.resolved_entity_ids, *valid_ids)))
        return self._knowledge_pack_engine.register_pack(
            pack_id,
            pack.name,
            pack.domain,
            taxonomy_root_id=pack.taxonomy_root_id,
            source_refs=pack.source_refs,
            update_rules=pack.update_rules,
            quality_controls=pack.quality_controls,
            knowledge_object_ids=pack.knowledge_object_ids,
            resolved_entity_ids=merged_ids,
            federated_relation_refs=pack.federated_relation_refs,
        )

    def attach_federated_relations(
        self, firm_id: str, pack_id: str, occurrences: Sequence[tuple[GraphOrigin, str]]
    ) -> KnowledgePack:
        pack = self._knowledge_pack_engine.get(pack_id)
        new_refs = {federated_relation_ref(origin, node_id) for origin, node_id in occurrences}
        merged_refs = tuple(dict.fromkeys((*pack.federated_relation_refs, *new_refs)))
        return self._knowledge_pack_engine.register_pack(
            pack_id,
            pack.name,
            pack.domain,
            taxonomy_root_id=pack.taxonomy_root_id,
            source_refs=pack.source_refs,
            update_rules=pack.update_rules,
            quality_controls=pack.quality_controls,
            knowledge_object_ids=pack.knowledge_object_ids,
            resolved_entity_ids=pack.resolved_entity_ids,
            federated_relation_refs=merged_refs,
        )

    def resolve_entities(self, firm_id: str, pack_id: str) -> list[ResolvedEntity]:
        pack = self._knowledge_pack_engine.get(pack_id)
        resolved = []
        for entity_id in pack.resolved_entity_ids:
            entity = self._entity_resolution.get(firm_id, entity_id)
            if entity is not None:
                resolved.append(entity)
        return resolved

    def resolve_federated_relations(
        self, firm_id: str, pack_id: str
    ) -> tuple[FederatedNeighborhood, ...]:
        pack = self._knowledge_pack_engine.get(pack_id)
        occurrences = [_parse_ref(ref) for ref in pack.federated_relation_refs]
        return self._federation.cross_scope_neighborhood(firm_id, occurrences)
