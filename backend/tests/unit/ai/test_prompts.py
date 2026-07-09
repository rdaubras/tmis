import pytest

from tmis.ai.prompts.registry import PromptRegistry


def test_register_starts_at_version_one() -> None:
    registry = PromptRegistry()
    prompt = registry.register(
        "analysis.extract_entities",
        category="analysis",
        template="Extract entities from: {text}",
        variables=("text",),
    )
    assert prompt.version == 1


def test_registering_same_id_again_increments_version() -> None:
    registry = PromptRegistry()
    registry.register("p", category="c", template="v1")
    second = registry.register("p", category="c", template="v2")
    assert second.version == 2
    assert registry.get("p").version == 2


def test_get_specific_version() -> None:
    registry = PromptRegistry()
    registry.register("p", category="c", template="v1")
    registry.register("p", category="c", template="v2")
    assert registry.get("p", version=1).template == "v1"


def test_get_unknown_prompt_raises_keyerror() -> None:
    registry = PromptRegistry()
    with pytest.raises(KeyError):
        registry.get("unknown")


def test_render_substitutes_variables() -> None:
    registry = PromptRegistry()
    registry.register(
        "greeting", category="chat", template="Bonjour {name}", variables=("name",)
    )
    assert registry.render("greeting", name="Maître Dupont") == "Bonjour Maître Dupont"


def test_render_missing_variable_raises_value_error() -> None:
    registry = PromptRegistry()
    registry.register(
        "greeting", category="chat", template="Bonjour {name}", variables=("name",)
    )
    with pytest.raises(ValueError, match="Missing variables"):
        registry.render("greeting")


def test_history_returns_every_version() -> None:
    registry = PromptRegistry()
    registry.register("p", category="c", template="v1")
    registry.register("p", category="c", template="v2")
    assert [p.version for p in registry.history("p")] == [1, 2]
