from tmis.legal_knowledge_graph.human_validation.schemas import GraphFeedback


class InMemoryGraphFeedbackStore:
    def __init__(self) -> None:
        self._feedback: list[GraphFeedback] = []

    def save(self, feedback: GraphFeedback) -> None:
        self._feedback.append(feedback)

    def list_for_subject(self, firm_id: str, subject_id: str) -> list[GraphFeedback]:
        return [
            f for f in self._feedback if f.firm_id == firm_id and f.subject_id == subject_id
        ]
