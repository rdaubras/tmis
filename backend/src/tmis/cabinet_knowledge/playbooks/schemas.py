import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeType


@dataclass(frozen=True, slots=True)
class PlaybookStep:
    order: int
    title: str
    description: str
    documents: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    vigilance_points: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Playbook:
    id: str
    case_type: str
    title: str
    steps: tuple[PlaybookStep, ...]
    checklist: tuple[str, ...] = ()


def new_playbook_instance_id() -> str:
    return f"pbi-{uuid.uuid4()}"


@dataclass(slots=True)
class PlaybookInstance:
    id: str
    firm_id: str
    playbook_id: str
    case_reference: str | None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_step_orders: frozenset[int] = frozenset()
    completed_at: datetime | None = None


def playbook_to_content(playbook: Playbook) -> dict[str, Any]:
    return {
        "case_type": playbook.case_type,
        "steps": [
            {
                "order": step.order,
                "title": step.title,
                "description": step.description,
                "documents": list(step.documents),
                "risks": list(step.risks),
                "vigilance_points": list(step.vigilance_points),
            }
            for step in playbook.steps
        ],
        "checklist": list(playbook.checklist),
    }


def playbook_from_knowledge_object(obj: KnowledgeObject) -> Playbook:
    if obj.type is not KnowledgeType.PLAYBOOK:
        raise ValueError(f"{obj.id} is not a playbook (type={obj.type.value})")
    steps = tuple(
        PlaybookStep(
            order=s["order"],
            title=s["title"],
            description=s["description"],
            documents=tuple(s.get("documents", ())),
            risks=tuple(s.get("risks", ())),
            vigilance_points=tuple(s.get("vigilance_points", ())),
        )
        for s in obj.content["steps"]
    )
    return Playbook(
        id=obj.id,
        case_type=obj.content["case_type"],
        title=obj.title,
        steps=steps,
        checklist=tuple(obj.content.get("checklist", ())),
    )
