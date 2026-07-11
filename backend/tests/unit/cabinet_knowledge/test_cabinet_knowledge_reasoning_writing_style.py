import pytest

from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.governance.store import InMemoryGovernanceStore
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.reasoning_patterns.engine import ReasoningPatternEngine
from tmis.cabinet_knowledge.writing_style.engine import (
    WritingStyleEngine,
    WritingStyleNotValidatedError,
)

FIRM = "firm-a"


def _space() -> KnowledgeSpace:
    return KnowledgeSpace(InMemoryKnowledgeStore())


def test_create_reasoning_pattern_roundtrip() -> None:
    engine = ReasoningPatternEngine(_space())

    created = engine.create_pattern(
        FIRM,
        "Prescription en matière prud'homale",
        context="licenciement contestation délai",
        strategy="Invoquer la prescription de 12 mois",
        arguments=("Article L1471-1 du Code du travail",),
        author="avocat1",
    )

    fetched = engine.get_pattern(FIRM, created.id)
    assert fetched.strategy == "Invoquer la prescription de 12 mois"
    assert fetched.confidence_level == 0.5


def test_find_applicable_matches_on_context_keywords() -> None:
    engine = ReasoningPatternEngine(_space())
    engine.create_pattern(
        FIRM,
        "Pattern social",
        context="licenciement contestation délai",
        strategy="...",
        arguments=(),
        author="a",
    )
    engine.create_pattern(
        FIRM,
        "Pattern commercial",
        context="recouvrement créance",
        strategy="...",
        arguments=(),
        author="a",
    )

    matches = engine.find_applicable(FIRM, ("licenciement",))

    assert [p.title for p in matches] == ["Pattern social"]


def test_writing_style_get_or_create_is_idempotent() -> None:
    engine = WritingStyleEngine(_space())

    first = engine.get_or_create_profile(FIRM, "avocat1")
    second = engine.get_or_create_profile(FIRM, "avocat1")

    assert first.id == second.id


def test_writing_style_update_merges_fields() -> None:
    engine = WritingStyleEngine(_space())
    engine.get_or_create_profile(FIRM, "avocat1")

    engine.update_profile(FIRM, "avocat1", vocabulary=("nonobstant",))
    updated = engine.update_profile(FIRM, "avocat1", signature_block="Bien cordialement,")

    assert updated.vocabulary == ("nonobstant",)
    assert updated.signature_block == "Bien cordialement,"


def test_apply_style_requires_validated_profile() -> None:
    space = _space()
    engine = WritingStyleEngine(space)
    engine.get_or_create_profile(FIRM, "avocat1")

    with pytest.raises(WritingStyleNotValidatedError):
        engine.apply_style(FIRM, "Cher client,")


def test_apply_style_appends_signature_once_validated() -> None:
    space = _space()
    engine = WritingStyleEngine(space)
    profile = engine.get_or_create_profile(FIRM, "avocat1")
    engine.update_profile(FIRM, "avocat1", signature_block="Bien cordialement,")
    governance = GovernanceEngine(InMemoryGovernanceStore(), space)
    governance.transition(FIRM, profile.id, KnowledgeStatus.IN_REVIEW, actor="a")
    governance.transition(FIRM, profile.id, KnowledgeStatus.VALIDATED, actor="a")

    result = engine.apply_style(FIRM, "Cher client,")

    assert result == "Cher client,\n\nBien cordialement,"
    result_again = engine.apply_style(FIRM, result)
    assert result_again == result
