from typing import Any

from tmis.cabinet_knowledge.feedback.ports import FeedbackStorePort
from tmis.cabinet_knowledge.feedback.schemas import Feedback, FeedbackAction, new_feedback_id
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.validation.engine import ValidationEngine
from tmis.cabinet_knowledge.validation.schemas import ValidationRequest


class FeedbackEngine:
    """The sprint's "FEEDBACK ENGINE": users accept, modify, reject,
    annotate or explain a knowledge object. Submitting feedback never
    mutates the knowledge base by itself — "chaque retour enrichit la
    base de connaissances après validation" — a `MODIFY` feedback can
    be turned into a real content revision via
    `apply_feedback_as_revision`, which immediately routes the
    revision back through `ValidationEngine` rather than promoting it
    directly."""

    def __init__(
        self,
        store: FeedbackStorePort,
        knowledge_space: KnowledgeSpace,
        validation: ValidationEngine,
    ) -> None:
        self._store = store
        self._knowledge_space = knowledge_space
        self._validation = validation

    def submit(
        self,
        firm_id: str,
        knowledge_object_id: str,
        action: FeedbackAction,
        author: str,
        comment: str = "",
    ) -> Feedback:
        if self._knowledge_space.get(firm_id, knowledge_object_id) is None:
            raise KeyError(knowledge_object_id)
        feedback = Feedback(
            id=new_feedback_id(),
            firm_id=firm_id,
            knowledge_object_id=knowledge_object_id,
            action=action,
            author=author,
            comment=comment,
        )
        self._store.save(feedback)
        return feedback

    def history_for(self, firm_id: str, knowledge_object_id: str) -> list[Feedback]:
        return self._store.list_for_object(firm_id, knowledge_object_id)

    def acceptance_rate(self, firm_id: str, knowledge_object_id: str) -> float:
        history = self.history_for(firm_id, knowledge_object_id)
        if not history:
            return 1.0
        accepted = sum(1 for f in history if f.action is FeedbackAction.ACCEPT)
        return accepted / len(history)

    def apply_feedback_as_revision(
        self,
        firm_id: str,
        feedback_id: str,
        new_content: dict[str, Any],
        reviewer: str,
    ) -> ValidationRequest:
        feedback = self._store.get(feedback_id)
        if feedback is None or feedback.firm_id != firm_id:
            raise KeyError(feedback_id)
        if feedback.action is not FeedbackAction.MODIFY:
            raise ValueError("Only MODIFY feedback can be turned into a revision")
        self._knowledge_space.update_content(
            firm_id, feedback.knowledge_object_id, new_content, actor=reviewer
        )
        return self._validation.submit_for_validation(
            firm_id, feedback.knowledge_object_id, requested_by=reviewer
        )
