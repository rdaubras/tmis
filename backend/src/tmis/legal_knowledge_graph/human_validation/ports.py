from typing import Protocol

from tmis.legal_knowledge_graph.human_validation.schemas import GraphFeedback


class GraphFeedbackStorePort(Protocol):
    def save(self, feedback: GraphFeedback) -> None: ...

    def list_for_subject(self, firm_id: str, subject_id: str) -> list[GraphFeedback]: ...
