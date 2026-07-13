import pytest

from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.legal_copilot_framework.reasoning_packs.engine import ReasoningPackEngine
from tmis.legal_copilot_framework.reasoning_packs.schemas import ReasoningStrategyType
from tmis.legal_copilot_framework.reasoning_packs.store import InMemoryReasoningPackStore

FIRM = "firm-a"


def _engine() -> tuple[ReasoningPackEngine, KnowledgeSpace]:
    space = KnowledgeSpace(InMemoryKnowledgeStore())
    return ReasoningPackEngine(InMemoryReasoningPackStore(), space), space


def test_register_pack_stores_strategy_types() -> None:
    engine, _ = _engine()
    strategies = frozenset(
        {ReasoningStrategyType.QUALIFICATION, ReasoningStrategyType.RISK_ANALYSIS}
    )

    pack = engine.register_pack("rp-1", "Pack", LegalDomain.CIVIL, strategies)

    assert pack.strategy_types == strategies
    assert pack.version == 1


def test_get_unknown_pack_raises_key_error() -> None:
    engine, _ = _engine()
    with pytest.raises(KeyError):
        engine.get("missing")


def test_resolve_patterns_returns_reasoning_patterns() -> None:
    engine, space = _engine()
    obj = space.create(
        FIRM,
        KnowledgeType.REASONING_PATTERN,
        "Pattern",
        {"context": "ctx", "strategy": "strat", "arguments": ["a1"]},
        "author",
    )
    engine.register_pack(
        "rp-1",
        "Pack",
        LegalDomain.CIVIL,
        frozenset({ReasoningStrategyType.QUALIFICATION}),
        pattern_ids=(obj.id,),
    )

    patterns = engine.resolve_patterns(FIRM, "rp-1")

    assert len(patterns) == 1
    assert patterns[0].context == "ctx"
    assert patterns[0].strategy == "strat"


def test_resolve_patterns_skips_ids_that_do_not_resolve() -> None:
    engine, _ = _engine()
    engine.register_pack(
        "rp-1", "Pack", LegalDomain.CIVIL, frozenset({ReasoningStrategyType.RISK_ANALYSIS}),
        pattern_ids=("unknown",),
    )

    assert engine.resolve_patterns(FIRM, "rp-1") == []
