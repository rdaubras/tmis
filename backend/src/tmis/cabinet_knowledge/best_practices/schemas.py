from dataclasses import dataclass
from typing import Any

from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeType
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain


@dataclass(frozen=True, slots=True)
class BestPractice:
    id: str
    title: str
    description: str
    domain: LegalDomain
    source: str
    applicability: tuple[str, ...] = ()


def best_practice_to_content(practice: BestPractice) -> dict[str, Any]:
    return {
        "description": practice.description,
        "domain": practice.domain.value,
        "source": practice.source,
        "applicability": list(practice.applicability),
    }


def best_practice_from_knowledge_object(obj: KnowledgeObject) -> BestPractice:
    if obj.type is not KnowledgeType.BEST_PRACTICE:
        raise ValueError(f"{obj.id} is not a best practice (type={obj.type.value})")
    return BestPractice(
        id=obj.id,
        title=obj.title,
        description=obj.content["description"],
        domain=LegalDomain(obj.content["domain"]),
        source=obj.content["source"],
        applicability=tuple(obj.content.get("applicability", ())),
    )
