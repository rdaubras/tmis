from tmis.legal_knowledge_graph.human_validation.ports import GraphFeedbackStorePort
from tmis.legal_knowledge_graph.human_validation.schemas import (
    FeedbackAction,
    GraphFeedback,
    new_graph_feedback_id,
)


class GraphFeedbackEngine:
    """Fills the one gap `cabinet_knowledge.feedback.FeedbackEngine`
    cannot: feedback on a graph relation or an entity-resolution
    match, neither of which is a `KnowledgeObject`. For any subject
    that *is* a `KnowledgeObject` (an ingested document, contract,
    note...), `FeedbackEngine` remains the engine of record — this
    class is never a second feedback mechanism for the same subject."""

    def __init__(self, store: GraphFeedbackStorePort) -> None:
        self._store = store

    def submit(
        self, firm_id: str, subject_id: str, action: FeedbackAction, author: str, comment: str = ""
    ) -> GraphFeedback:
        feedback = GraphFeedback(
            id=new_graph_feedback_id(),
            firm_id=firm_id,
            subject_id=subject_id,
            action=action,
            author=author,
            comment=comment,
        )
        self._store.save(feedback)
        return feedback

    def history_for(self, firm_id: str, subject_id: str) -> list[GraphFeedback]:
        return self._store.list_for_subject(firm_id, subject_id)

    def acceptance_rate(self, firm_id: str, subject_id: str) -> float:
        history = self.history_for(firm_id, subject_id)
        if not history:
            return 1.0
        accepted = sum(1 for f in history if f.action is FeedbackAction.ACCEPT)
        return accepted / len(history)
