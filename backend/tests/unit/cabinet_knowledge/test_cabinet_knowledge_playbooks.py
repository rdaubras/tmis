import pytest

from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.governance.store import InMemoryGovernanceStore
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.playbooks.engine import PlaybookEngine, PlaybookNotValidatedError
from tmis.cabinet_knowledge.playbooks.schemas import PlaybookStep
from tmis.cabinet_knowledge.playbooks.store import InMemoryPlaybookInstanceStore

FIRM = "firm-a"

_STEPS = (
    PlaybookStep(1, "Entretien client", "Recueillir les faits"),
    PlaybookStep(2, "Constitution du dossier", "Rassembler les pièces"),
)


def _space() -> KnowledgeSpace:
    return KnowledgeSpace(InMemoryKnowledgeStore())


def _engine(space: KnowledgeSpace) -> PlaybookEngine:
    return PlaybookEngine(space, InMemoryPlaybookInstanceStore())


def _validate(space: KnowledgeSpace, object_id: str) -> None:
    governance = GovernanceEngine(InMemoryGovernanceStore(), space)
    governance.transition(FIRM, object_id, KnowledgeStatus.IN_REVIEW, actor="a")
    governance.transition(FIRM, object_id, KnowledgeStatus.VALIDATED, actor="a")


def test_create_and_roundtrip_playbook() -> None:
    space = _space()
    engine = _engine(space)

    created = engine.create_playbook(
        FIRM, "Ouverture prud'homale", "prudhommes", _STEPS, ("Vérifier délais",), "avocat1"
    )
    fetched = engine.get_playbook(FIRM, created.id)

    assert fetched.title == "Ouverture prud'homale"
    assert len(fetched.steps) == 2
    assert fetched.checklist == ("Vérifier délais",)


def test_list_playbooks_filters_by_case_type() -> None:
    space = _space()
    engine = _engine(space)
    engine.create_playbook(FIRM, "A", "prudhommes", _STEPS, (), "avocat1")
    engine.create_playbook(FIRM, "B", "recouvrement", _STEPS, (), "avocat1")

    assert [p.title for p in engine.list_playbooks(FIRM, case_type="prudhommes")] == ["A"]


def test_start_instance_requires_validated_playbook() -> None:
    space = _space()
    engine = _engine(space)
    playbook = engine.create_playbook(FIRM, "A", "prudhommes", _STEPS, (), "avocat1")

    with pytest.raises(PlaybookNotValidatedError):
        engine.start_instance(FIRM, playbook.id, "dossier-1")


def test_start_instance_records_usage() -> None:
    space = _space()
    engine = _engine(space)
    playbook = engine.create_playbook(FIRM, "A", "prudhommes", _STEPS, (), "avocat1")
    _validate(space, playbook.id)

    engine.start_instance(FIRM, playbook.id, "dossier-1")

    obj = space.get(FIRM, playbook.id)
    assert obj is not None
    assert obj.usage_count == 1


def test_complete_step_tracks_progress_and_completion() -> None:
    space = _space()
    engine = _engine(space)
    playbook = engine.create_playbook(FIRM, "A", "prudhommes", _STEPS, (), "avocat1")
    _validate(space, playbook.id)
    instance = engine.start_instance(FIRM, playbook.id, "dossier-1")

    assert engine.progress(FIRM, instance.id) == 0.0

    engine.complete_step(FIRM, instance.id, 1)
    assert engine.progress(FIRM, instance.id) == 0.5

    completed = engine.complete_step(FIRM, instance.id, 2)
    assert engine.progress(FIRM, instance.id) == 1.0
    assert completed.completed_at is not None


def test_complete_step_rejects_unknown_step_order() -> None:
    space = _space()
    engine = _engine(space)
    playbook = engine.create_playbook(FIRM, "A", "prudhommes", _STEPS, (), "avocat1")
    _validate(space, playbook.id)
    instance = engine.start_instance(FIRM, playbook.id, "dossier-1")

    with pytest.raises(ValueError, match="Unknown step order"):
        engine.complete_step(FIRM, instance.id, 99)
