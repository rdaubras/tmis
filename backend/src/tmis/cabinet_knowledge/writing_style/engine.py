from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus, KnowledgeType
from tmis.cabinet_knowledge.writing_style.schemas import (
    WritingStyleProfile,
    profile_from_knowledge_object,
    profile_to_content,
)


class WritingStyleNotValidatedError(ValueError):
    pass


class WritingStyleEngine:
    """The sprint's "WRITING STYLE ENGINE" — one `WritingStyleProfile`
    knowledge object per firm. `apply_style` is deliberately a
    deterministic transformation (append the validated signature
    block), not an LLM rewrite: adapting an agent's drafting *voice*
    to the profile is a Legal Drafting Studio (Sprint 7) concern for a
    future sprint, kept out of scope here to avoid touching Sprint 7
    code (see docs/reports/sprint-12-axes-amelioration-sprint-13.md)."""

    def __init__(self, knowledge_space: KnowledgeSpace) -> None:
        self._knowledge_space = knowledge_space

    def get_or_create_profile(self, firm_id: str, author: str) -> WritingStyleProfile:
        existing = self._knowledge_space.list(firm_id, type_=KnowledgeType.WRITING_STYLE)
        if existing:
            return profile_from_knowledge_object(existing[0])
        blank = WritingStyleProfile(id="")
        obj = self._knowledge_space.create(
            firm_id,
            KnowledgeType.WRITING_STYLE,
            title=f"Style rédactionnel — {firm_id}",
            content=profile_to_content(blank),
            author=author,
        )
        return profile_from_knowledge_object(obj)

    def update_profile(
        self,
        firm_id: str,
        actor: str,
        vocabulary: tuple[str, ...] | None = None,
        favorite_expressions: tuple[str, ...] | None = None,
        structure_preferences: tuple[str, ...] | None = None,
        signature_block: str | None = None,
    ) -> WritingStyleProfile:
        current = self.get_or_create_profile(firm_id, actor)
        updated = WritingStyleProfile(
            id=current.id,
            vocabulary=vocabulary if vocabulary is not None else current.vocabulary,
            favorite_expressions=(
                favorite_expressions
                if favorite_expressions is not None
                else current.favorite_expressions
            ),
            structure_preferences=(
                structure_preferences
                if structure_preferences is not None
                else current.structure_preferences
            ),
            signature_block=(
                signature_block if signature_block is not None else current.signature_block
            ),
        )
        obj = self._knowledge_space.update_content(
            firm_id, current.id, profile_to_content(updated), actor
        )
        return profile_from_knowledge_object(obj)

    def apply_style(self, firm_id: str, draft_text: str) -> str:
        objects = self._knowledge_space.list(firm_id, type_=KnowledgeType.WRITING_STYLE)
        if not objects or objects[0].status is not KnowledgeStatus.VALIDATED:
            raise WritingStyleNotValidatedError(
                f"No validated writing style profile for firm {firm_id!r}"
            )
        profile = profile_from_knowledge_object(objects[0])
        self._knowledge_space.record_usage(firm_id, profile.id)
        if profile.signature_block and profile.signature_block not in draft_text:
            return f"{draft_text}\n\n{profile.signature_block}"
        return draft_text
