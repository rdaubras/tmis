from datetime import UTC, datetime
from typing import Any

import structlog

from tmis.cabinet_knowledge.knowledge.ports import KnowledgeStorePort
from tmis.cabinet_knowledge.knowledge.schemas import (
    KnowledgeObject,
    KnowledgeStatus,
    KnowledgeType,
    new_knowledge_id,
)
from tmis.platform.metrics.bootstrap import get_metrics_registry
from tmis.platform.security.tenant_isolation import TenantContext, require_same_firm

_logger = structlog.get_logger(__name__)


class KnowledgeSpace:
    """The single, tenant-scoped entry point onto a firm's knowledge —
    every other engine in `cabinet_knowledge` reads and writes through
    this facade rather than touching `KnowledgeStorePort` directly, so
    tenant isolation (see the sprint's "isolation stricte" constraint)
    is enforced in exactly one place, mirroring the `KernelPort`
    single-chokepoint pattern from Sprint 11's `tmis.ai_team`.

    A new object always starts life as `DRAFT` — nothing in this class
    can create or promote a knowledge object straight to `VALIDATED`;
    that transition is only reachable through
    `tmis.cabinet_knowledge.validation`, which requires an explicit
    human decision (see the sprint constraint "aucune connaissance ne
    peut être ajoutée automatiquement sans validation humaine").
    """

    def __init__(self, store: KnowledgeStorePort) -> None:
        self._store = store

    def create(
        self,
        firm_id: str,
        type_: KnowledgeType,
        title: str,
        content: dict[str, Any],
        author: str,
        tags: frozenset[str] = frozenset(),
    ) -> KnowledgeObject:
        obj = KnowledgeObject(
            id=new_knowledge_id(),
            firm_id=firm_id,
            type=type_,
            title=title,
            content=content,
            author=author,
            tags=tags,
        )
        self._store.save(obj)
        _logger.info(
            "cabinet_knowledge.enriched",
            firm_id=firm_id,
            knowledge_object_id=obj.id,
            type=type_.value,
            author=author,
        )
        get_metrics_registry().counter(
            "cabinet_knowledge_enrichments_total", "Total knowledge objects created (always DRAFT)"
        ).inc(type=type_.value)
        return obj

    def get(self, firm_id: str, object_id: str) -> KnowledgeObject | None:
        obj = self._store.get(object_id)
        if obj is None:
            return None
        require_same_firm(
            TenantContext(firm_id=firm_id, actor_id="system"), obj.firm_id
        )
        return obj

    def list(
        self,
        firm_id: str,
        type_: KnowledgeType | None = None,
        status: KnowledgeStatus | None = None,
    ) -> list[KnowledgeObject]:
        objects = self._store.list_for_firm(firm_id, type_)
        if status is not None:
            objects = [obj for obj in objects if obj.status is status]
        return objects

    def update_content(
        self, firm_id: str, object_id: str, content: dict[str, Any], actor: str
    ) -> KnowledgeObject:
        """Any substantive content change demotes the object back to
        `DRAFT`, regardless of its previous status — a `VALIDATED`
        knowledge object never silently stays validated after its
        content changes; it must go through
        `tmis.cabinet_knowledge.validation` again."""
        obj = self.get(firm_id, object_id)
        if obj is None:
            raise KeyError(object_id)
        obj.content = content
        obj.version += 1
        obj.status = KnowledgeStatus.DRAFT
        obj.is_published = False
        obj.updated_at = datetime.now(UTC)
        self._store.save(obj)
        return obj

    def add_tags(
        self, firm_id: str, object_id: str, tags: frozenset[str]
    ) -> KnowledgeObject:
        """Tagging is metadata, not substantive content — it never
        resets governance status, unlike `update_content`."""
        obj = self.get(firm_id, object_id)
        if obj is None:
            raise KeyError(object_id)
        obj.tags = obj.tags | tags
        obj.updated_at = datetime.now(UTC)
        self._store.save(obj)
        return obj

    def set_quality_score(
        self, firm_id: str, object_id: str, score: float
    ) -> KnowledgeObject:
        obj = self.get(firm_id, object_id)
        if obj is None:
            raise KeyError(object_id)
        obj.quality_score = score
        self._store.save(obj)
        return obj

    def set_status(
        self, firm_id: str, object_id: str, status: KnowledgeStatus
    ) -> KnowledgeObject:
        """Raw status mutation used exclusively by
        `tmis.cabinet_knowledge.governance.GovernanceEngine`, which is
        the only caller allowed to decide *which* transitions are
        legal — this method trusts its caller and does not re-check
        `ALLOWED_TRANSITIONS` itself, to avoid a circular import
        between `knowledge` and `governance`."""
        obj = self.get(firm_id, object_id)
        if obj is None:
            raise KeyError(object_id)
        obj.status = status
        if status is not KnowledgeStatus.VALIDATED:
            obj.is_published = False
        obj.updated_at = datetime.now(UTC)
        self._store.save(obj)
        return obj

    def record_usage(self, firm_id: str, object_id: str) -> KnowledgeObject:
        """Called wherever a knowledge object is actually *applied* to
        a real matter (a playbook instantiated, a clause variant
        pulled into a draft, a recommendation acted on) — never on a
        mere search, so `usage_count` keeps a single, meaningful
        semantic: real reuse, not lookups."""
        obj = self.get(firm_id, object_id)
        if obj is None:
            raise KeyError(object_id)
        obj.usage_count += 1
        self._store.save(obj)
        _logger.info(
            "cabinet_knowledge.reused",
            firm_id=firm_id,
            knowledge_object_id=object_id,
            usage_count=obj.usage_count,
        )
        get_metrics_registry().counter(
            "cabinet_knowledge_reuse_total",
            "Total times a knowledge object was applied to a matter",
        ).inc(type=obj.type.value)
        return obj
