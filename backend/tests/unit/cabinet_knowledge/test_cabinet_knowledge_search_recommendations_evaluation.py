from tmis.cabinet_knowledge.evaluation.engine import EvaluationEngine
from tmis.cabinet_knowledge.feedback.engine import FeedbackEngine
from tmis.cabinet_knowledge.feedback.store import InMemoryFeedbackStore
from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.governance.store import InMemoryGovernanceStore
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus, KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.recommendations.engine import RecommendationEngine
from tmis.cabinet_knowledge.recommendations.schemas import RecommendationContext
from tmis.cabinet_knowledge.search.engine import SearchEngine
from tmis.cabinet_knowledge.search.schemas import SearchQuery
from tmis.cabinet_knowledge.validation.engine import ValidationEngine
from tmis.cabinet_knowledge.validation.store import InMemoryValidationStore

FIRM = "firm-a"


def _space() -> KnowledgeSpace:
    return KnowledgeSpace(InMemoryKnowledgeStore())


def _publish(space: KnowledgeSpace, object_id: str) -> None:
    governance = GovernanceEngine(InMemoryGovernanceStore(), space)
    governance.transition(FIRM, object_id, KnowledgeStatus.IN_REVIEW, actor="a")
    governance.transition(FIRM, object_id, KnowledgeStatus.VALIDATED, actor="a")
    obj = space.get(FIRM, object_id)
    assert obj is not None
    obj.is_published = True


def test_search_filters_by_status_and_keyword() -> None:
    space = _space()
    draft = space.create(FIRM, KnowledgeType.NOTE, "Note brouillon", {"text": "prescription"}, "a")
    validated = space.create(FIRM, KnowledgeType.NOTE, "Note validee", {"text": "..."}, "a")
    _publish(space, validated.id)
    search = SearchEngine(space)

    validated_only = search.search(FIRM, SearchQuery(status=KnowledgeStatus.VALIDATED))
    assert [o.id for o in validated_only] == [validated.id]

    by_keyword = search.search(FIRM, SearchQuery(keyword="prescription"))
    assert [o.id for o in by_keyword] == [draft.id]


def test_search_never_records_usage() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "a")
    SearchEngine(space).search(FIRM, SearchQuery())

    reloaded = space.get(FIRM, obj.id)
    assert reloaded is not None
    assert reloaded.usage_count == 0


def test_recommendations_only_include_published_validated_objects() -> None:
    space = _space()
    draft = space.create(FIRM, KnowledgeType.NOTE, "Draft", {"text": "prescription"}, "a")
    validated = space.create(FIRM, KnowledgeType.NOTE, "Validated", {"text": "prescription"}, "a")
    _publish(space, validated.id)
    engine = RecommendationEngine(space, SearchEngine(space))

    recs = engine.recommend(FIRM, RecommendationContext(keywords=("prescription",)))

    assert [r.knowledge_object_id for r in recs] == [validated.id]
    assert draft.id not in [r.knowledge_object_id for r in recs]


def test_recommendations_are_explainable() -> None:
    space = _space()
    validated = space.create(FIRM, KnowledgeType.NOTE, "Validated", {"text": "prescription"}, "a")
    _publish(space, validated.id)
    engine = RecommendationEngine(space, SearchEngine(space))

    recs = engine.recommend(FIRM, RecommendationContext(keywords=("prescription",)))

    assert recs[0].explanation
    assert "prescription" in recs[0].explanation


def test_recommendations_record_usage() -> None:
    space = _space()
    validated = space.create(FIRM, KnowledgeType.NOTE, "Validated", {"text": "prescription"}, "a")
    _publish(space, validated.id)
    engine = RecommendationEngine(space, SearchEngine(space))

    engine.recommend(FIRM, RecommendationContext(keywords=("prescription",)))

    reloaded = space.get(FIRM, validated.id)
    assert reloaded is not None
    assert reloaded.usage_count == 1


def test_evaluation_aggregates_firm_stats() -> None:
    space = _space()
    validated = space.create(FIRM, KnowledgeType.NOTE, "V", {}, "a")
    _publish(space, validated.id)
    space.create(FIRM, KnowledgeType.NOTE, "D", {}, "a")
    validation = ValidationEngine(
        InMemoryValidationStore(), space, GovernanceEngine(InMemoryGovernanceStore(), space)
    )
    feedback = FeedbackEngine(InMemoryFeedbackStore(), space, validation)
    evaluation = EvaluationEngine(space, feedback)

    result = evaluation.evaluate_firm(FIRM)

    assert result.total_objects == 2
    assert result.by_status["validated"] == 1
    assert result.by_status["draft"] == 1
    assert result.validation_rate == 0.5
