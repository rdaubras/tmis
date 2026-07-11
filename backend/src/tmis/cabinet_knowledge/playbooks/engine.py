from datetime import UTC, datetime

from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus, KnowledgeType
from tmis.cabinet_knowledge.playbooks.ports import PlaybookInstanceStorePort
from tmis.cabinet_knowledge.playbooks.schemas import (
    Playbook,
    PlaybookInstance,
    PlaybookStep,
    new_playbook_instance_id,
    playbook_from_knowledge_object,
    playbook_to_content,
)


class PlaybookNotValidatedError(ValueError):
    pass


class PlaybookEngine:
    """Playbooks are stored as `KnowledgeObject`s of type `PLAYBOOK`
    (typed (de)serialization in `playbooks/schemas.py`); this engine
    adds the behavior the sprint asks for beyond CRUD: instantiating a
    playbook against a real matter and tracking checklist/step
    progress."""

    def __init__(
        self, knowledge_space: KnowledgeSpace, instance_store: PlaybookInstanceStorePort
    ) -> None:
        self._knowledge_space = knowledge_space
        self._instance_store = instance_store

    def create_playbook(
        self,
        firm_id: str,
        title: str,
        case_type: str,
        steps: tuple[PlaybookStep, ...],
        checklist: tuple[str, ...],
        author: str,
    ) -> Playbook:
        playbook_shell = Playbook(
            id="", case_type=case_type, title=title, steps=steps, checklist=checklist
        )
        obj = self._knowledge_space.create(
            firm_id,
            KnowledgeType.PLAYBOOK,
            title,
            playbook_to_content(playbook_shell),
            author,
            tags=frozenset({case_type}),
        )
        return playbook_from_knowledge_object(obj)

    def get_playbook(self, firm_id: str, playbook_id: str) -> Playbook:
        obj = self._knowledge_space.get(firm_id, playbook_id)
        if obj is None:
            raise KeyError(playbook_id)
        return playbook_from_knowledge_object(obj)

    def list_playbooks(self, firm_id: str, case_type: str | None = None) -> list[Playbook]:
        objects = self._knowledge_space.list(firm_id, type_=KnowledgeType.PLAYBOOK)
        playbooks = [playbook_from_knowledge_object(obj) for obj in objects]
        if case_type is not None:
            playbooks = [p for p in playbooks if p.case_type == case_type]
        return playbooks

    def start_instance(
        self, firm_id: str, playbook_id: str, case_reference: str | None
    ) -> PlaybookInstance:
        obj = self._knowledge_space.get(firm_id, playbook_id)
        if obj is None:
            raise KeyError(playbook_id)
        if obj.status is not KnowledgeStatus.VALIDATED:
            raise PlaybookNotValidatedError(
                f"Playbook {playbook_id} is {obj.status.value}, expected validated"
            )
        self._knowledge_space.record_usage(firm_id, playbook_id)
        instance = PlaybookInstance(
            id=new_playbook_instance_id(),
            firm_id=firm_id,
            playbook_id=playbook_id,
            case_reference=case_reference,
        )
        self._instance_store.save(instance)
        return instance

    def complete_step(
        self, firm_id: str, instance_id: str, step_order: int
    ) -> PlaybookInstance:
        instance = self._instance_store.get(instance_id)
        if instance is None or instance.firm_id != firm_id:
            raise KeyError(instance_id)
        playbook = self.get_playbook(firm_id, instance.playbook_id)
        if step_order not in {s.order for s in playbook.steps}:
            raise ValueError(f"Unknown step order {step_order} for playbook {playbook.id}")
        instance.completed_step_orders = instance.completed_step_orders | {step_order}
        if len(instance.completed_step_orders) == len(playbook.steps):
            instance.completed_at = datetime.now(UTC)
        self._instance_store.save(instance)
        return instance

    def progress(self, firm_id: str, instance_id: str) -> float:
        instance = self._instance_store.get(instance_id)
        if instance is None or instance.firm_id != firm_id:
            raise KeyError(instance_id)
        playbook = self.get_playbook(firm_id, instance.playbook_id)
        if not playbook.steps:
            return 1.0
        return len(instance.completed_step_orders) / len(playbook.steps)
