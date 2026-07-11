from typing import Protocol

from tmis.cabinet_knowledge.feedback.schemas import Feedback


class FeedbackStorePort(Protocol):
    def save(self, feedback: Feedback) -> None: ...

    def get(self, feedback_id: str) -> Feedback | None: ...

    def list_for_object(self, firm_id: str, knowledge_object_id: str) -> list[Feedback]: ...
