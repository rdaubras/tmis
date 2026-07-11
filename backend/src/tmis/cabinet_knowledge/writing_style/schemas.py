from dataclasses import dataclass
from typing import Any

from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeType


@dataclass(frozen=True, slots=True)
class WritingStyleProfile:
    id: str
    vocabulary: tuple[str, ...] = ()
    favorite_expressions: tuple[str, ...] = ()
    structure_preferences: tuple[str, ...] = ()
    signature_block: str = ""


def profile_to_content(profile: WritingStyleProfile) -> dict[str, Any]:
    return {
        "vocabulary": list(profile.vocabulary),
        "favorite_expressions": list(profile.favorite_expressions),
        "structure_preferences": list(profile.structure_preferences),
        "signature_block": profile.signature_block,
    }


def profile_from_knowledge_object(obj: KnowledgeObject) -> WritingStyleProfile:
    if obj.type is not KnowledgeType.WRITING_STYLE:
        raise ValueError(f"{obj.id} is not a writing style profile (type={obj.type.value})")
    return WritingStyleProfile(
        id=obj.id,
        vocabulary=tuple(obj.content.get("vocabulary", ())),
        favorite_expressions=tuple(obj.content.get("favorite_expressions", ())),
        structure_preferences=tuple(obj.content.get("structure_preferences", ())),
        signature_block=obj.content.get("signature_block", ""),
    )
