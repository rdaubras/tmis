from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject
from tmis.legal_copilot_framework.knowledge_packs.ports import KnowledgePackStorePort
from tmis.legal_copilot_framework.knowledge_packs.schemas import KnowledgePack


class KnowledgePackEngine:
    """Composes `cabinet_knowledge.knowledge.KnowledgeSpace` (Sprint
    12) rather than a second knowledge store — a `KnowledgePack` is
    only a named, versioned pointer into a firm's existing knowledge,
    resolved fresh on every call so it always reflects the current
    governance status of each object."""

    def __init__(self, store: KnowledgePackStorePort, knowledge_space: KnowledgeSpace) -> None:
        self._store = store
        self._knowledge_space = knowledge_space

    def register_pack(
        self,
        pack_id: str,
        name: str,
        domain: LegalDomain,
        *,
        taxonomy_root_id: str | None = None,
        source_refs: tuple[str, ...] = (),
        update_rules: tuple[str, ...] = (),
        quality_controls: tuple[str, ...] = (),
        knowledge_object_ids: tuple[str, ...] = (),
        resolved_entity_ids: tuple[str, ...] = (),
        federated_relation_refs: tuple[str, ...] = (),
    ) -> KnowledgePack:
        existing = self._store.history(pack_id)
        version = existing[-1].version + 1 if existing else 1
        pack = KnowledgePack(
            id=pack_id,
            name=name,
            domain=domain,
            version=version,
            taxonomy_root_id=taxonomy_root_id,
            source_refs=source_refs,
            update_rules=update_rules,
            quality_controls=quality_controls,
            knowledge_object_ids=knowledge_object_ids,
            resolved_entity_ids=resolved_entity_ids,
            federated_relation_refs=federated_relation_refs,
        )
        self._store.save(pack)
        return pack

    def get(self, pack_id: str, version: int | None = None) -> KnowledgePack:
        pack = self._store.get(pack_id, version)
        if pack is None:
            raise KeyError(pack_id)
        return pack

    def resolve_objects(self, firm_id: str, pack_id: str) -> list[KnowledgeObject]:
        pack = self.get(pack_id)
        resolved = []
        for object_id in pack.knowledge_object_ids:
            obj = self._knowledge_space.get(firm_id, object_id)
            if obj is not None:
                resolved.append(obj)
        return resolved
