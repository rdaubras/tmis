from tmis.cabinet_knowledge.bootstrap import get_playbook_engine, get_recommendation_engine
from tmis.cabinet_knowledge.recommendations.schemas import RecommendationContext
from tmis.strategic_intelligence.playbooks.adapter import PlaybookAdapter
from tmis.strategic_intelligence.recommendations.engine import StrategicRecommendationEngine
from tmis.strategic_intelligence.recommendations.schemas import SimilarStrategyRecommendation
from tmis.strategic_intelligence.tradeoffs.engine import TradeoffEngine


def test_tradeoff_engine_computes_shared_risks() -> None:
    engine = TradeoffEngine()

    analysis = engine.compare(
        "strategy-1",
        "strategy-2",
        advantages_a=("Rapide",),
        advantages_b=("Exhaustif",),
        risks_a=("Rejet", "Délai long"),
        risks_b=("Délai long",),
    )

    assert analysis.shared_risks == ("Délai long",)


def test_tradeoff_engine_never_declares_a_winner() -> None:
    engine = TradeoffEngine()

    analysis = engine.compare("strategy-1", "strategy-2")

    assert not hasattr(analysis, "winner")
    assert not hasattr(analysis, "recommended")


def test_playbook_adapter_wraps_cabinet_knowledge_engine_directly() -> None:
    adapter = PlaybookAdapter(get_playbook_engine())

    playbooks = adapter.find_playbooks_for_case_type("firm-test-si", "unknown-case-type")

    assert playbooks == []


def test_playbook_adapter_steps_as_recommended_actions_reads_titles() -> None:
    from tmis.cabinet_knowledge.playbooks.schemas import Playbook, PlaybookStep

    adapter = PlaybookAdapter(get_playbook_engine())
    playbook = Playbook(
        id="pb-1",
        case_type="licenciement",
        title="Playbook licenciement",
        steps=(
            PlaybookStep(1, "Analyser le dossier", "desc", (), (), ()),
            PlaybookStep(2, "Envoyer mise en demeure", "desc", (), (), ()),
        ),
        checklist=(),
    )

    steps = adapter.steps_as_recommended_actions(playbook)

    assert steps == ("Analyser le dossier", "Envoyer mise en demeure")


def test_strategic_recommendation_engine_composes_cabinet_knowledge_and_learning() -> None:
    engine = StrategicRecommendationEngine(get_recommendation_engine())
    similar = (
        SimilarStrategyRecommendation("strategy-old-1", "Négociation amiable", "explication"),
    )

    recommendations = engine.recommend(
        "firm-test-si", RecommendationContext(domain_tag=None, keywords=()), similar
    )

    assert recommendations.similar_strategies == similar
    assert isinstance(recommendations.knowledge_recommendation_ids, tuple)
