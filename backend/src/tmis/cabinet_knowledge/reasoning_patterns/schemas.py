from dataclasses import dataclass
from typing import Any

from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeType


@dataclass(frozen=True, slots=True)
class ReasoningPattern:
    id: str
    title: str
    context: str
    strategy: str
    arguments: tuple[str, ...]
    counter_arguments: tuple[str, ...] = ()
    references: tuple[str, ...] = ()
    confidence_level: float = 0.5


def pattern_to_content(pattern: ReasoningPattern) -> dict[str, Any]:
    return {
        "context": pattern.context,
        "strategy": pattern.strategy,
        "arguments": list(pattern.arguments),
        "counter_arguments": list(pattern.counter_arguments),
        "references": list(pattern.references),
        "confidence_level": pattern.confidence_level,
    }


def pattern_from_knowledge_object(obj: KnowledgeObject) -> ReasoningPattern:
    if obj.type is not KnowledgeType.REASONING_PATTERN:
        raise ValueError(f"{obj.id} is not a reasoning pattern (type={obj.type.value})")
    return ReasoningPattern(
        id=obj.id,
        title=obj.title,
        context=obj.content["context"],
        strategy=obj.content["strategy"],
        arguments=tuple(obj.content["arguments"]),
        counter_arguments=tuple(obj.content.get("counter_arguments", ())),
        references=tuple(obj.content.get("references", ())),
        confidence_level=obj.content.get("confidence_level", 0.5),
    )
