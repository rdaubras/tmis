from datetime import UTC, datetime

from tmis.cabinet_knowledge.feedback.engine import FeedbackEngine
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeStatus
from tmis.cabinet_knowledge.quality.schemas import QualityBreakdown

_FRESHNESS_HALF_LIFE_DAYS = 365
_USAGE_SATURATION = 10


class QualityEngine:
    """The sprint's "QUALITY ENGINE": freshness, complétude, fréquence
    d'utilisation, validation humaine, cohérence — each in [0, 1], and
    an `overall` average persisted back onto the object's
    `quality_score` (a metadata write, not a content change; see
    `KnowledgeSpace.set_quality_score`)."""

    def __init__(
        self,
        knowledge_space: KnowledgeSpace,
        feedback: FeedbackEngine,
    ) -> None:
        self._knowledge_space = knowledge_space
        self._feedback = feedback

    def evaluate(self, firm_id: str, obj: KnowledgeObject) -> QualityBreakdown:
        age_days = (datetime.now(UTC) - obj.updated_at).days
        freshness = max(0.0, 1.0 - age_days / _FRESHNESS_HALF_LIFE_DAYS)

        completeness_signals = [bool(obj.title), bool(obj.content), bool(obj.tags)]
        completeness = sum(completeness_signals) / len(completeness_signals)

        usage = min(1.0, obj.usage_count / _USAGE_SATURATION)

        human_validation = {
            KnowledgeStatus.VALIDATED: 1.0,
            KnowledgeStatus.OBSOLETE: 1.0,
            KnowledgeStatus.IN_REVIEW: 0.5,
        }.get(obj.status, 0.0)

        coherence = self._feedback.acceptance_rate(firm_id, obj.id)

        return QualityBreakdown(
            knowledge_object_id=obj.id,
            freshness=freshness,
            completeness=completeness,
            usage=usage,
            human_validation=human_validation,
            coherence=coherence,
        )

    def evaluate_and_store(self, firm_id: str, knowledge_object_id: str) -> QualityBreakdown:
        obj = self._knowledge_space.get(firm_id, knowledge_object_id)
        if obj is None:
            raise KeyError(knowledge_object_id)
        breakdown = self.evaluate(firm_id, obj)
        self._knowledge_space.set_quality_score(firm_id, knowledge_object_id, breakdown.overall)
        return breakdown
