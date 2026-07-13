import pytest

from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.legal_copilot_framework.copilot.engine import CopilotEngine
from tmis.legal_copilot_framework.copilot.schemas import LegalCopilot
from tmis.legal_copilot_framework.copilot.store import (
    InMemoryCopilotActivationStore,
    InMemoryCopilotStore,
)

FIRM = "firm-a"


def _copilot(copilot_id: str = "copilot-1") -> LegalCopilot:
    return LegalCopilot(
        id=copilot_id,
        name="Copilote",
        domain=LegalDomain.CIVIL,
        description="desc",
        version="1.0.0",
        dependencies=(),
        team_id="team-1",
        compatible_models=frozenset(),
        prompt_pack_id=None,
        knowledge_pack_ids=(),
        reasoning_pack_ids=(),
        document_pack_ids=(),
        workflow_pack_ids=(),
        validation_policy_ids=(),
        permissions=frozenset(),
    )


def _engine() -> CopilotEngine:
    return CopilotEngine(InMemoryCopilotStore(), InMemoryCopilotActivationStore())


def test_define_and_get_roundtrip() -> None:
    engine = _engine()
    copilot = _copilot()
    engine.define(copilot)

    assert engine.get("copilot-1") == copilot


def test_get_unknown_copilot_raises_key_error() -> None:
    engine = _engine()
    with pytest.raises(KeyError):
        engine.get("missing")


def test_list_all_returns_every_defined_copilot() -> None:
    engine = _engine()
    engine.define(_copilot("copilot-1"))
    engine.define(_copilot("copilot-2"))

    assert {c.id for c in engine.list_all()} == {"copilot-1", "copilot-2"}


def test_activate_requires_the_copilot_to_exist() -> None:
    engine = _engine()
    with pytest.raises(KeyError):
        engine.activate(FIRM, "missing")


def test_activate_then_deactivate_toggles_is_active() -> None:
    engine = _engine()
    engine.define(_copilot())

    assert engine.is_active(FIRM, "copilot-1") is False

    engine.activate(FIRM, "copilot-1")
    assert engine.is_active(FIRM, "copilot-1") is True

    engine.deactivate(FIRM, "copilot-1")
    assert engine.is_active(FIRM, "copilot-1") is False


def test_active_copilots_only_lists_activated_ones_for_that_firm() -> None:
    engine = _engine()
    engine.define(_copilot("copilot-1"))
    engine.define(_copilot("copilot-2"))
    engine.activate(FIRM, "copilot-1")

    assert [c.id for c in engine.active_copilots(FIRM)] == ["copilot-1"]
    assert engine.active_copilots("other-firm") == []
