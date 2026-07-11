import pytest

from tmis.cabinet_knowledge.bootstrap import (
    get_approval_engine,
    get_evaluation_engine,
    get_feedback_engine,
    get_knowledge_space,
    get_lineage_engine,
    get_playbook_engine,
    get_quality_engine,
    get_recommendation_engine,
    get_search_engine,
    get_validation_engine,
)
from tmis.cabinet_knowledge.feedback.schemas import FeedbackAction
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus, KnowledgeType
from tmis.cabinet_knowledge.playbooks.schemas import PlaybookStep
from tmis.cabinet_knowledge.recommendations.schemas import RecommendationContext
from tmis.cabinet_knowledge.search.schemas import SearchQuery
from tmis.cabinet_knowledge.validation.schemas import ValidationDecision
from tmis.platform.security.tenant_isolation import TenantAccessError


def test_full_governance_pipeline_draft_to_published() -> None:
    """Mirrors a real cabinet workflow end to end, entirely through
    the process-wide bootstrap singletons: create (DRAFT) -> submit
    for validation (IN_REVIEW) -> approve (VALIDATED) -> publish
    (visible to search/recommendations)."""
    firm_id = "firm-pipeline-1"
    knowledge_space = get_knowledge_space()

    obj = knowledge_space.create(
        firm_id,
        KnowledgeType.BEST_PRACTICE,
        "Vérifier le délai de prescription",
        {"description": "toujours vérifier avant d'ouvrir un dossier", "domain": "civil"},
        author="avocat1",
    )
    assert obj.status is KnowledgeStatus.DRAFT

    request = get_validation_engine().submit_for_validation(
        firm_id, obj.id, requested_by="avocat1"
    )
    decided = get_validation_engine().decide(
        firm_id, request.id, ValidationDecision.APPROVE, reviewer="associe1"
    )
    assert decided.status.value == "approved"

    published = get_approval_engine().publish(firm_id, obj.id, approver="associe1")
    assert published.is_published is True

    found = get_search_engine().search(firm_id, SearchQuery(published_only=True))
    assert obj.id in [o.id for o in found]

    recs = get_recommendation_engine().recommend(
        firm_id, RecommendationContext(keywords=("prescription",))
    )
    assert obj.id in [r.knowledge_object_id for r in recs]


def test_feedback_driven_revision_returns_to_review_not_straight_to_validated() -> None:
    """A MODIFY feedback never re-validates a knowledge object by
    itself — it always lands back in IN_REVIEW, requiring a fresh
    human `decide(APPROVE)` (see the sprint's "aucune connaissance ne
    peut être ajoutée automatiquement sans validation humaine")."""
    firm_id = "firm-pipeline-2"
    knowledge_space = get_knowledge_space()
    validation = get_validation_engine()
    feedback = get_feedback_engine()

    obj = knowledge_space.create(
        firm_id, KnowledgeType.NOTE, "Note interne", {"text": "v1"}, author="avocat1"
    )
    request = validation.submit_for_validation(firm_id, obj.id, requested_by="avocat1")
    validation.decide(firm_id, request.id, ValidationDecision.APPROVE, reviewer="associe1")
    assert knowledge_space.get(firm_id, obj.id).status is KnowledgeStatus.VALIDATED  # type: ignore[union-attr]

    fb = feedback.submit(firm_id, obj.id, FeedbackAction.MODIFY, author="avocat2", comment="v2 svp")
    revision_request = feedback.apply_feedback_as_revision(
        firm_id, fb.id, {"text": "v2"}, reviewer="associe1"
    )

    reloaded = knowledge_space.get(firm_id, obj.id)
    assert reloaded is not None
    assert reloaded.status is KnowledgeStatus.IN_REVIEW
    assert reloaded.is_published is False

    revalidated = validation.decide(
        firm_id, revision_request.id, ValidationDecision.APPROVE, reviewer="associe1"
    )
    assert revalidated.status.value == "approved"
    assert knowledge_space.get(firm_id, obj.id).status is KnowledgeStatus.VALIDATED  # type: ignore[union-attr]


def test_playbook_instance_and_quality_and_lineage_and_evaluation_flow() -> None:
    firm_id = "firm-pipeline-3"
    validation = get_validation_engine()
    playbooks = get_playbook_engine()

    playbook = playbooks.create_playbook(
        firm_id,
        "Ouverture dossier prud'homal",
        "prudhommes",
        (
            PlaybookStep(1, "Entretien client", "Recueillir les faits"),
            PlaybookStep(2, "Constitution du dossier", "Rassembler les pièces"),
        ),
        ("Vérifier le délai de prescription",),
        author="avocat1",
    )
    request = validation.submit_for_validation(firm_id, playbook.id, requested_by="avocat1")
    validation.decide(firm_id, request.id, ValidationDecision.APPROVE, reviewer="associe1")

    instance = playbooks.start_instance(firm_id, playbook.id, "dossier-123")
    playbooks.complete_step(firm_id, instance.id, 1)
    playbooks.complete_step(firm_id, instance.id, 2)
    assert playbooks.progress(firm_id, instance.id) == 1.0

    quality = get_quality_engine().evaluate_and_store(firm_id, playbook.id)
    assert quality.human_validation == 1.0

    lineage = get_lineage_engine().explain(firm_id, playbook.id)
    assert lineage.current_version == 1

    evaluation = get_evaluation_engine().evaluate_firm(firm_id)
    assert evaluation.total_objects == 1
    assert evaluation.validation_rate == 1.0
    assert playbook.id in evaluation.most_reused


def test_tenant_isolation_across_two_firms() -> None:
    firm_a = "firm-isolation-a"
    firm_b = "firm-isolation-b"
    knowledge_space = get_knowledge_space()

    obj_a = knowledge_space.create(firm_a, KnowledgeType.NOTE, "A", {}, author="avocat-a")
    knowledge_space.create(firm_b, KnowledgeType.NOTE, "B", {}, author="avocat-b")

    with pytest.raises(TenantAccessError):
        knowledge_space.get(firm_b, obj_a.id)

    assert [o.title for o in knowledge_space.list(firm_a)] == ["A"]
    assert [o.title for o in knowledge_space.list(firm_b)] == ["B"]

    with pytest.raises(TenantAccessError):
        get_validation_engine().submit_for_validation(firm_b, obj_a.id, requested_by="avocat-b")
