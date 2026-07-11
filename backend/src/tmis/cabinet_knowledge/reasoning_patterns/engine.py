from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.cabinet_knowledge.reasoning_patterns.schemas import (
    ReasoningPattern,
    pattern_from_knowledge_object,
    pattern_to_content,
)


class ReasoningPatternEngine:
    """The sprint's reusable "REASONING PATTERNS" library. Patterns
    are stored as `KnowledgeObject`s; nothing here calls into
    `tmis.legal_reasoning` (Sprint 6) — wiring a validated pattern
    into `ReasoningOrchestrator` is left as a documented Sprint 13+
    integration point (see docs/reports/sprint-12-axes-amelioration-
    sprint-13.md) so this sprint never modifies Sprint 6 code."""

    def __init__(self, knowledge_space: KnowledgeSpace) -> None:
        self._knowledge_space = knowledge_space

    def create_pattern(
        self,
        firm_id: str,
        title: str,
        context: str,
        strategy: str,
        arguments: tuple[str, ...],
        author: str,
        counter_arguments: tuple[str, ...] = (),
        references: tuple[str, ...] = (),
        confidence_level: float = 0.5,
    ) -> ReasoningPattern:
        pattern_shell = ReasoningPattern(
            id="",
            title=title,
            context=context,
            strategy=strategy,
            arguments=arguments,
            counter_arguments=counter_arguments,
            references=references,
            confidence_level=confidence_level,
        )
        obj = self._knowledge_space.create(
            firm_id,
            KnowledgeType.REASONING_PATTERN,
            title,
            pattern_to_content(pattern_shell),
            author,
        )
        return pattern_from_knowledge_object(obj)

    def get_pattern(self, firm_id: str, pattern_id: str) -> ReasoningPattern:
        obj = self._knowledge_space.get(firm_id, pattern_id)
        if obj is None:
            raise KeyError(pattern_id)
        return pattern_from_knowledge_object(obj)

    def list_patterns(self, firm_id: str) -> list[ReasoningPattern]:
        objects = self._knowledge_space.list(firm_id, type_=KnowledgeType.REASONING_PATTERN)
        return [pattern_from_knowledge_object(obj) for obj in objects]

    def find_applicable(
        self, firm_id: str, context_keywords: tuple[str, ...]
    ) -> list[ReasoningPattern]:
        needles = {kw.lower() for kw in context_keywords}
        return [
            p
            for p in self.list_patterns(firm_id)
            if needles & set(p.context.lower().split())
        ]
