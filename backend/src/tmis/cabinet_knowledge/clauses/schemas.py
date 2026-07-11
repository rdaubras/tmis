from dataclasses import dataclass
from typing import Any

from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeType
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain


@dataclass(frozen=True, slots=True)
class ClauseVariant:
    id: str
    text: str
    notes: str = ""
    language: str = "fr"


@dataclass(frozen=True, slots=True)
class Clause:
    id: str
    domain: LegalDomain
    clause_type: str
    title: str
    variants: tuple[ClauseVariant, ...]
    comments: tuple[str, ...] = ()
    jurisprudence_refs: tuple[str, ...] = ()


def clause_to_content(clause: Clause) -> dict[str, Any]:
    return {
        "domain": clause.domain.value,
        "clause_type": clause.clause_type,
        "variants": [
            {"id": v.id, "text": v.text, "notes": v.notes, "language": v.language}
            for v in clause.variants
        ],
        "comments": list(clause.comments),
        "jurisprudence_refs": list(clause.jurisprudence_refs),
    }


def clause_from_knowledge_object(obj: KnowledgeObject) -> Clause:
    if obj.type is not KnowledgeType.CLAUSE:
        raise ValueError(f"{obj.id} is not a clause (type={obj.type.value})")
    variants = tuple(
        ClauseVariant(
            id=v["id"], text=v["text"], notes=v.get("notes", ""), language=v.get("language", "fr")
        )
        for v in obj.content["variants"]
    )
    return Clause(
        id=obj.id,
        domain=LegalDomain(obj.content["domain"]),
        clause_type=obj.content["clause_type"],
        title=obj.title,
        variants=variants,
        comments=tuple(obj.content.get("comments", ())),
        jurisprudence_refs=tuple(obj.content.get("jurisprudence_refs", ())),
    )
