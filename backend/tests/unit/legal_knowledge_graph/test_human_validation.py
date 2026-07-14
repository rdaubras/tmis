from tmis.legal_knowledge_graph.human_validation.engine import GraphFeedbackEngine
from tmis.legal_knowledge_graph.human_validation.schemas import FeedbackAction
from tmis.legal_knowledge_graph.human_validation.store import InMemoryGraphFeedbackStore

FIRM = "firm-a"
SUBJECT = "relation-1"


def _engine() -> GraphFeedbackEngine:
    return GraphFeedbackEngine(InMemoryGraphFeedbackStore())


def test_acceptance_rate_of_unreviewed_subject_defaults_to_one() -> None:
    engine = _engine()

    assert engine.acceptance_rate(FIRM, SUBJECT) == 1.0


def test_submit_records_feedback_and_history() -> None:
    engine = _engine()
    feedback = engine.submit(FIRM, SUBJECT, FeedbackAction.ACCEPT, "Camille Lefèvre", "confirmé")

    history = engine.history_for(FIRM, SUBJECT)

    assert feedback.action is FeedbackAction.ACCEPT
    assert [f.id for f in history] == [feedback.id]


def test_acceptance_rate_reflects_mixed_feedback() -> None:
    engine = _engine()
    engine.submit(FIRM, SUBJECT, FeedbackAction.ACCEPT, "Camille Lefèvre")
    engine.submit(FIRM, SUBJECT, FeedbackAction.ANNOTATE, "Julien Moreau")
    engine.submit(FIRM, SUBJECT, FeedbackAction.REJECT, "Julien Moreau")

    assert engine.acceptance_rate(FIRM, SUBJECT) == 1 / 3


def test_history_is_scoped_per_subject() -> None:
    engine = _engine()
    engine.submit(FIRM, SUBJECT, FeedbackAction.ACCEPT, "Camille Lefèvre")
    engine.submit(FIRM, "relation-2", FeedbackAction.REJECT, "Julien Moreau")

    assert len(engine.history_for(FIRM, SUBJECT)) == 1
