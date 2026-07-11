from tmis.cabinet_knowledge.feedback.schemas import Feedback


class InMemoryFeedbackStore:
    def __init__(self) -> None:
        self._feedback: list[Feedback] = []

    def save(self, feedback: Feedback) -> None:
        self._feedback.append(feedback)

    def get(self, feedback_id: str) -> Feedback | None:
        return next((f for f in self._feedback if f.id == feedback_id), None)

    def list_for_object(self, firm_id: str, knowledge_object_id: str) -> list[Feedback]:
        return [
            f
            for f in self._feedback
            if f.firm_id == firm_id and f.knowledge_object_id == knowledge_object_id
        ]
