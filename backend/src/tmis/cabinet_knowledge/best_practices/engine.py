from tmis.cabinet_knowledge.best_practices.schemas import (
    BestPractice,
    best_practice_from_knowledge_object,
    best_practice_to_content,
)
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain


class BestPracticeEngine:
    def __init__(self, knowledge_space: KnowledgeSpace) -> None:
        self._knowledge_space = knowledge_space

    def create(
        self,
        firm_id: str,
        title: str,
        description: str,
        domain: LegalDomain,
        source: str,
        author: str,
        applicability: tuple[str, ...] = (),
    ) -> BestPractice:
        shell = BestPractice(
            id="",
            title=title,
            description=description,
            domain=domain,
            source=source,
            applicability=applicability,
        )
        obj = self._knowledge_space.create(
            firm_id,
            KnowledgeType.BEST_PRACTICE,
            title,
            best_practice_to_content(shell),
            author,
            tags=frozenset({domain.value}),
        )
        return best_practice_from_knowledge_object(obj)

    def get(self, firm_id: str, practice_id: str) -> BestPractice:
        obj = self._knowledge_space.get(firm_id, practice_id)
        if obj is None:
            raise KeyError(practice_id)
        return best_practice_from_knowledge_object(obj)

    def list(self, firm_id: str, domain: LegalDomain | None = None) -> list[BestPractice]:
        objects = self._knowledge_space.list(firm_id, type_=KnowledgeType.BEST_PRACTICE)
        practices = [best_practice_from_knowledge_object(obj) for obj in objects]
        if domain is not None:
            practices = [p for p in practices if p.domain is domain]
        return practices
