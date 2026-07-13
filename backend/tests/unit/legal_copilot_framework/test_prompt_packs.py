import pytest

from tmis.ai.prompts.registry import PromptRegistry
from tmis.ai_fabric.capabilities.schemas import Capability
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor
from tmis.ai_fabric.prompt_optimizer.engine import PromptOptimizer
from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.legal_copilot_framework.prompt_packs.engine import PromptPackEngine
from tmis.legal_copilot_framework.prompt_packs.store import InMemoryPromptPackStore


def _engine() -> tuple[PromptPackEngine, PromptRegistry]:
    registry = PromptRegistry()
    engine = PromptPackEngine(InMemoryPromptPackStore(), registry, PromptOptimizer(registry))
    return engine, registry


def test_register_pack_versions_increment() -> None:
    engine, _ = _engine()
    first = engine.register_pack("pp-1", "Pack", LegalDomain.CIVIL)
    second = engine.register_pack("pp-1", "Pack", LegalDomain.CIVIL)

    assert first.version == 1
    assert second.version == 2
    assert engine.history("pp-1") == [first, second]
    assert engine.get("pp-1") == second
    assert engine.get("pp-1", version=1) == first


def test_get_unknown_pack_raises_key_error() -> None:
    engine, _ = _engine()
    with pytest.raises(KeyError):
        engine.get("missing")


def test_resolve_prompt_id_falls_back_to_base_id_without_override() -> None:
    engine, _ = _engine()
    engine.register_pack("pp-1", "Pack", LegalDomain.CIVIL, system_prompt_ids=("base-prompt",))

    assert engine.resolve_prompt_id("pp-1", "base-prompt") == "base-prompt"


def test_resolve_prompt_id_honours_pack_override() -> None:
    engine, _ = _engine()
    engine.register_pack(
        "pp-1", "Pack", LegalDomain.CIVIL, overrides={"base-prompt": "override-prompt"}
    )

    assert engine.resolve_prompt_id("pp-1", "base-prompt") == "override-prompt"


def test_resolve_prompt_id_falls_back_to_parent_pack_override() -> None:
    engine, _ = _engine()
    engine.register_pack(
        "parent", "Parent", LegalDomain.CIVIL, overrides={"base": "parent-override"}
    )
    engine.register_pack("child", "Child", LegalDomain.CIVIL, parent_pack_id="parent")

    assert engine.resolve_prompt_id("child", "base") == "parent-override"


def test_render_uses_resolved_prompt_id() -> None:
    engine, registry = _engine()
    registry.register(
        "base-prompt", category="system", template="Bonjour {name}", variables=("name",)
    )
    registry.register(
        "override-prompt", category="system", template="Salut {name}", variables=("name",)
    )
    engine.register_pack(
        "pp-1", "Pack", LegalDomain.CIVIL, overrides={"base-prompt": "override-prompt"}
    )

    assert engine.render("pp-1", "base-prompt", name="Ada") == "Salut Ada"


def test_render_for_model_adapts_the_rendered_prompt() -> None:
    engine, registry = _engine()
    registry.register(
        "base-prompt", category="system", template="Bonjour {name}", variables=("name",)
    )
    engine.register_pack("pp-1", "Pack", LegalDomain.CIVIL, system_prompt_ids=("base-prompt",))
    model = ModelDescriptor(
        name="GPT-4o",
        version="2024-08",
        provider="openai",
        cost_per_1k_tokens_usd=0.005,
        avg_latency_ms=800.0,
        max_context_tokens=128_000,
        capabilities=frozenset({Capability.TEXT_COMPLETION}),
    )

    optimized = engine.render_for_model("pp-1", "base-prompt", model, name="Ada")

    assert "Ada" in optimized.text
