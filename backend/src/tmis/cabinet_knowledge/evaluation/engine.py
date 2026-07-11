from tmis.cabinet_knowledge.evaluation.schemas import KnowledgeBaseEvaluation
from tmis.cabinet_knowledge.feedback.engine import FeedbackEngine
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus

_TOP_REUSED_LIMIT = 5


class EvaluationEngine:
    def __init__(self, knowledge_space: KnowledgeSpace, feedback: FeedbackEngine) -> None:
        self._knowledge_space = knowledge_space
        self._feedback = feedback

    def evaluate_firm(self, firm_id: str) -> KnowledgeBaseEvaluation:
        objects = self._knowledge_space.list(firm_id)
        by_status: dict[str, int] = {}
        for obj in objects:
            by_status[obj.status.value] = by_status.get(obj.status.value, 0) + 1

        total = len(objects)
        validated = by_status.get(KnowledgeStatus.VALIDATED.value, 0)
        validation_rate = validated / total if total else 0.0

        average_quality_score = sum(obj.quality_score for obj in objects) / total if total else 0.0

        most_reused = tuple(
            obj.id
            for obj in sorted(objects, key=lambda o: o.usage_count, reverse=True)[
                :_TOP_REUSED_LIMIT
            ]
            if obj.usage_count > 0
        )

        acceptance_rates = [self._feedback.acceptance_rate(firm_id, obj.id) for obj in objects]
        feedback_acceptance_rate = (
            sum(acceptance_rates) / len(acceptance_rates) if acceptance_rates else 1.0
        )

        return KnowledgeBaseEvaluation(
            firm_id=firm_id,
            total_objects=total,
            by_status=by_status,
            validation_rate=validation_rate,
            average_quality_score=average_quality_score,
            most_reused=most_reused,
            feedback_acceptance_rate=feedback_acceptance_rate,
        )
