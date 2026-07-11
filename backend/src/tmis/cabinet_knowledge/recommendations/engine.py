import structlog

from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.recommendations.schemas import Recommendation, RecommendationContext
from tmis.cabinet_knowledge.search.engine import SearchEngine
from tmis.cabinet_knowledge.search.schemas import SearchQuery
from tmis.platform.metrics.bootstrap import get_metrics_registry

_logger = structlog.get_logger(__name__)
_QUALITY_WEIGHT = 0.5


class RecommendationEngine:
    """The sprint's "RECOMMENDATION ENGINE" — only recommends
    `VALIDATED` and published knowledge (never a draft), and every
    recommendation carries a human-readable `explanation`, satisfying
    "les recommandations doivent toujours être explicables". Returning
    a recommendation counts as reuse (`KnowledgeSpace.record_usage`),
    unlike a plain search."""

    def __init__(self, knowledge_space: KnowledgeSpace, search: SearchEngine) -> None:
        self._knowledge_space = knowledge_space
        self._search = search

    def recommend(
        self, firm_id: str, context: RecommendationContext, limit: int = 5
    ) -> list[Recommendation]:
        candidates = self._search.search(
            firm_id, SearchQuery(tag=context.domain_tag, published_only=True)
        )
        keywords = {kw.lower() for kw in context.keywords}
        scored: list[Recommendation] = []
        for obj in candidates:
            haystack = f"{obj.title} {obj.content}".lower()
            matched_keywords = {kw for kw in keywords if kw in haystack}
            keyword_score = len(matched_keywords) / len(keywords) if keywords else 0.0
            score = keyword_score * 0.5 + obj.quality_score * _QUALITY_WEIGHT
            if keywords and not matched_keywords:
                continue
            reasons = []
            if context.domain_tag:
                reasons.append(f"correspond au domaine « {context.domain_tag} »")
            if matched_keywords:
                reasons.append(f"mots-clés en commun : {', '.join(sorted(matched_keywords))}")
            if obj.quality_score > 0:
                reasons.append(f"qualité évaluée à {obj.quality_score:.2f}")
            explanation = "; ".join(reasons) or "connaissance publiée du cabinet"
            scored.append(
                Recommendation(
                    knowledge_object_id=obj.id,
                    object_type=obj.type,
                    title=obj.title,
                    score=score,
                    explanation=explanation,
                )
            )
        scored.sort(key=lambda r: r.score, reverse=True)
        top = scored[:limit]
        for recommendation in top:
            self._knowledge_space.record_usage(firm_id, recommendation.knowledge_object_id)
        _logger.info(
            "cabinet_knowledge.recommended", firm_id=firm_id, recommendation_count=len(top)
        )
        get_metrics_registry().counter(
            "cabinet_knowledge_recommendations_total", "Total recommendations returned"
        ).inc(amount=len(top))
        return top
