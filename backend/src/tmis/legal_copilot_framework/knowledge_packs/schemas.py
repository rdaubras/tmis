from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.ai_team.capabilities.schemas import LegalDomain


@dataclass(frozen=True, slots=True)
class KnowledgePack:
    """A named, versioned selection of `cabinet_knowledge.knowledge.
    KnowledgeObject`s (playbooks, clauses, reasoning patterns, writing
    style...) for one legal domain. Never a second knowledge store —
    `knowledge_object_ids` are ids resolved through the firm's own
    `KnowledgeSpace` (Sprint 12), so governance/versioning/tenant
    isolation are never duplicated."""

    id: str
    name: str
    domain: LegalDomain
    version: int
    taxonomy_root_id: str | None = None
    source_refs: tuple[str, ...] = ()
    update_rules: tuple[str, ...] = ()
    quality_controls: tuple[str, ...] = ()
    knowledge_object_ids: tuple[str, ...] = ()
    # Added in Sprint 25 (Knowledge Graph Federation) — additive only:
    # a pack may also point at entities resolved across the three
    # existing graphs (`knowledge_graph.entity_resolution.
    # ResolvedEntity.id`) and at federated cross-scope relation refs
    # (`"{GraphOrigin}:{node_id}"`), resolved fresh through
    # `knowledge_graph.copilot_bridge` rather than copied here.
    resolved_entity_ids: tuple[str, ...] = ()
    federated_relation_refs: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
