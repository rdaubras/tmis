from tmis.cabinet_knowledge.clauses.schemas import (
    Clause,
    ClauseVariant,
    clause_from_knowledge_object,
    clause_to_content,
)
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain


class ClauseEngine:
    """The sprint's "CLAUSE LIBRARY". Clauses are `KnowledgeObject`s
    of type `CLAUSE`; `search` is a clause-specific convenience over
    `KnowledgeSpace.list` (domain/type/keyword), distinct from the
    cross-type `tmis.cabinet_knowledge.search` engine."""

    def __init__(self, knowledge_space: KnowledgeSpace) -> None:
        self._knowledge_space = knowledge_space

    def create_clause(
        self,
        firm_id: str,
        title: str,
        domain: LegalDomain,
        clause_type: str,
        variants: tuple[ClauseVariant, ...],
        author: str,
        comments: tuple[str, ...] = (),
        jurisprudence_refs: tuple[str, ...] = (),
    ) -> Clause:
        clause_shell = Clause(
            id="",
            domain=domain,
            clause_type=clause_type,
            title=title,
            variants=variants,
            comments=comments,
            jurisprudence_refs=jurisprudence_refs,
        )
        obj = self._knowledge_space.create(
            firm_id,
            KnowledgeType.CLAUSE,
            title,
            clause_to_content(clause_shell),
            author,
            tags=frozenset({domain.value, clause_type}),
        )
        return clause_from_knowledge_object(obj)

    def get_clause(self, firm_id: str, clause_id: str, mark_used: bool = False) -> Clause:
        obj = self._knowledge_space.get(firm_id, clause_id)
        if obj is None:
            raise KeyError(clause_id)
        if mark_used:
            self._knowledge_space.record_usage(firm_id, clause_id)
        return clause_from_knowledge_object(obj)

    def add_variant(
        self, firm_id: str, clause_id: str, variant: ClauseVariant, actor: str
    ) -> Clause:
        clause = self.get_clause(firm_id, clause_id)
        updated = Clause(
            id=clause.id,
            domain=clause.domain,
            clause_type=clause.clause_type,
            title=clause.title,
            variants=(*clause.variants, variant),
            comments=clause.comments,
            jurisprudence_refs=clause.jurisprudence_refs,
        )
        obj = self._knowledge_space.update_content(
            firm_id, clause_id, clause_to_content(updated), actor
        )
        return clause_from_knowledge_object(obj)

    def search(
        self,
        firm_id: str,
        domain: LegalDomain | None = None,
        clause_type: str | None = None,
        keyword: str | None = None,
    ) -> list[Clause]:
        objects = self._knowledge_space.list(firm_id, type_=KnowledgeType.CLAUSE)
        clauses = [clause_from_knowledge_object(obj) for obj in objects]
        if domain is not None:
            clauses = [c for c in clauses if c.domain is domain]
        if clause_type is not None:
            clauses = [c for c in clauses if c.clause_type == clause_type]
        if keyword is not None:
            needle = keyword.lower()
            clauses = [
                c
                for c in clauses
                if needle in c.title.lower()
                or any(needle in v.text.lower() for v in c.variants)
            ]
        return clauses
