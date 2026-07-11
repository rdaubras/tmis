from functools import lru_cache

from tmis.cabinet_knowledge.approval.engine import ApprovalEngine
from tmis.cabinet_knowledge.approval.store import InMemoryApprovalStore
from tmis.cabinet_knowledge.best_practices.engine import BestPracticeEngine
from tmis.cabinet_knowledge.clauses.engine import ClauseEngine
from tmis.cabinet_knowledge.evaluation.engine import EvaluationEngine
from tmis.cabinet_knowledge.feedback.engine import FeedbackEngine
from tmis.cabinet_knowledge.feedback.store import InMemoryFeedbackStore
from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.governance.store import InMemoryGovernanceStore
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.lessons_learned.engine import LessonLearnedEngine
from tmis.cabinet_knowledge.lineage.engine import LineageEngine
from tmis.cabinet_knowledge.lineage.store import InMemoryLineageStore
from tmis.cabinet_knowledge.ontology.engine import OntologyEngine
from tmis.cabinet_knowledge.ontology.store import InMemoryRelationStore
from tmis.cabinet_knowledge.playbooks.engine import PlaybookEngine
from tmis.cabinet_knowledge.playbooks.store import InMemoryPlaybookInstanceStore
from tmis.cabinet_knowledge.quality.engine import QualityEngine
from tmis.cabinet_knowledge.reasoning_patterns.engine import ReasoningPatternEngine
from tmis.cabinet_knowledge.recommendations.engine import RecommendationEngine
from tmis.cabinet_knowledge.search.engine import SearchEngine
from tmis.cabinet_knowledge.taxonomy.engine import TaxonomyEngine, seed_default_taxonomy
from tmis.cabinet_knowledge.taxonomy.store import InMemoryTaxonomyStore
from tmis.cabinet_knowledge.templates.engine import CabinetTemplateEngine
from tmis.cabinet_knowledge.validation.engine import ValidationEngine
from tmis.cabinet_knowledge.validation.store import InMemoryValidationStore
from tmis.cabinet_knowledge.writing_style.engine import WritingStyleEngine


@lru_cache
def get_knowledge_store() -> InMemoryKnowledgeStore:
    return InMemoryKnowledgeStore()


@lru_cache
def get_knowledge_space() -> KnowledgeSpace:
    """The process-wide composition root for `tmis.cabinet_knowledge`
    (see docs/59-architecture-cabinet-knowledge-engine.md) — every
    engine below is wired against this single `KnowledgeSpace`
    instance, so a firm's knowledge is consistent regardless of which
    specialized engine reads or writes it."""
    return KnowledgeSpace(get_knowledge_store())


@lru_cache
def get_relation_store() -> InMemoryRelationStore:
    return InMemoryRelationStore()


@lru_cache
def get_ontology_engine() -> OntologyEngine:
    return OntologyEngine(get_relation_store(), get_knowledge_space())


@lru_cache
def get_taxonomy_store() -> InMemoryTaxonomyStore:
    store = InMemoryTaxonomyStore()
    seed_default_taxonomy(store)
    return store


@lru_cache
def get_taxonomy_engine() -> TaxonomyEngine:
    return TaxonomyEngine(get_taxonomy_store(), get_knowledge_space())


@lru_cache
def get_governance_store() -> InMemoryGovernanceStore:
    return InMemoryGovernanceStore()


@lru_cache
def get_governance_engine() -> GovernanceEngine:
    return GovernanceEngine(get_governance_store(), get_knowledge_space())


@lru_cache
def get_validation_store() -> InMemoryValidationStore:
    return InMemoryValidationStore()


@lru_cache
def get_validation_engine() -> ValidationEngine:
    return ValidationEngine(get_validation_store(), get_knowledge_space(), get_governance_engine())


@lru_cache
def get_lineage_store() -> InMemoryLineageStore:
    return InMemoryLineageStore()


@lru_cache
def get_lineage_engine() -> LineageEngine:
    return LineageEngine(get_lineage_store(), get_knowledge_space(), get_governance_engine())


@lru_cache
def get_approval_store() -> InMemoryApprovalStore:
    return InMemoryApprovalStore()


@lru_cache
def get_approval_engine() -> ApprovalEngine:
    return ApprovalEngine(get_approval_store(), get_knowledge_space())


@lru_cache
def get_feedback_store() -> InMemoryFeedbackStore:
    return InMemoryFeedbackStore()


@lru_cache
def get_feedback_engine() -> FeedbackEngine:
    return FeedbackEngine(get_feedback_store(), get_knowledge_space(), get_validation_engine())


@lru_cache
def get_quality_engine() -> QualityEngine:
    return QualityEngine(get_knowledge_space(), get_feedback_engine())


@lru_cache
def get_playbook_instance_store() -> InMemoryPlaybookInstanceStore:
    return InMemoryPlaybookInstanceStore()


@lru_cache
def get_playbook_engine() -> PlaybookEngine:
    return PlaybookEngine(get_knowledge_space(), get_playbook_instance_store())


@lru_cache
def get_template_engine() -> CabinetTemplateEngine:
    return CabinetTemplateEngine(get_knowledge_space())


@lru_cache
def get_clause_engine() -> ClauseEngine:
    return ClauseEngine(get_knowledge_space())


@lru_cache
def get_reasoning_pattern_engine() -> ReasoningPatternEngine:
    return ReasoningPatternEngine(get_knowledge_space())


@lru_cache
def get_writing_style_engine() -> WritingStyleEngine:
    return WritingStyleEngine(get_knowledge_space())


@lru_cache
def get_best_practice_engine() -> BestPracticeEngine:
    return BestPracticeEngine(get_knowledge_space())


@lru_cache
def get_lesson_learned_engine() -> LessonLearnedEngine:
    return LessonLearnedEngine(get_knowledge_space())


@lru_cache
def get_search_engine() -> SearchEngine:
    return SearchEngine(get_knowledge_space())


@lru_cache
def get_recommendation_engine() -> RecommendationEngine:
    return RecommendationEngine(get_knowledge_space(), get_search_engine())


@lru_cache
def get_evaluation_engine() -> EvaluationEngine:
    return EvaluationEngine(get_knowledge_space(), get_feedback_engine())
