import pytest

from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.legal_copilot_framework.knowledge_packs.engine import KnowledgePackEngine
from tmis.legal_copilot_framework.knowledge_packs.store import InMemoryKnowledgePackStore

FIRM = "firm-a"


def _engine() -> tuple[KnowledgePackEngine, KnowledgeSpace]:
    space = KnowledgeSpace(InMemoryKnowledgeStore())
    return KnowledgePackEngine(InMemoryKnowledgePackStore(), space), space


def test_register_pack_versions_increment() -> None:
    engine, _ = _engine()
    first = engine.register_pack("kp-1", "Pack", LegalDomain.CIVIL)
    second = engine.register_pack("kp-1", "Pack", LegalDomain.CIVIL)

    assert first.version == 1
    assert second.version == 2
    assert engine.get("kp-1") == second


def test_get_unknown_pack_raises_key_error() -> None:
    engine, _ = _engine()
    with pytest.raises(KeyError):
        engine.get("missing")


def test_resolve_objects_returns_referenced_knowledge() -> None:
    engine, space = _engine()
    obj = space.create(FIRM, KnowledgeType.PLAYBOOK, "Playbook", {"steps": ["a"]}, "author")
    engine.register_pack("kp-1", "Pack", LegalDomain.CIVIL, knowledge_object_ids=(obj.id,))

    resolved = engine.resolve_objects(FIRM, "kp-1")

    assert [o.id for o in resolved] == [obj.id]


def test_resolve_objects_skips_ids_that_do_not_resolve() -> None:
    engine, _ = _engine()
    engine.register_pack("kp-1", "Pack", LegalDomain.CIVIL, knowledge_object_ids=("unknown-id",))

    assert engine.resolve_objects(FIRM, "kp-1") == []
