import structlog

from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject
from tmis.cabinet_knowledge.search.schemas import SearchQuery
from tmis.platform.metrics.bootstrap import get_metrics_registry

_logger = structlog.get_logger(__name__)


class SearchEngine:
    """Advanced, cross-type search over a firm's `KnowledgeSpace` (see
    the sprint's "SEARCH" API requirement). Deliberately side-effect
    free — it never calls `KnowledgeSpace.record_usage`, so browsing
    results never inflates "réutilisation" statistics; only actually
    *applying* a piece of knowledge does (see `knowledge/engine.py`)."""

    def __init__(self, knowledge_space: KnowledgeSpace) -> None:
        self._knowledge_space = knowledge_space

    def search(self, firm_id: str, query: SearchQuery) -> list[KnowledgeObject]:
        objects = self._knowledge_space.list(firm_id, type_=query.type, status=query.status)
        if query.tag is not None:
            objects = [obj for obj in objects if query.tag in obj.tags]
        if query.published_only:
            objects = [obj for obj in objects if obj.is_published]
        if query.keyword is not None:
            needle = query.keyword.lower()
            objects = [
                obj
                for obj in objects
                if needle in obj.title.lower() or needle in str(obj.content).lower()
            ]
        _logger.info(
            "cabinet_knowledge.searched", firm_id=firm_id, result_count=len(objects)
        )
        get_metrics_registry().counter(
            "cabinet_knowledge_searches_total", "Total knowledge searches"
        ).inc()
        return objects
