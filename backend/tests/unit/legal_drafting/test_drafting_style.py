from tmis.legal_drafting.style.engine import StyleEngine
from tmis.legal_drafting.style.registry import StyleProfileRegistry
from tmis.legal_drafting.style.schemas import StyleProfile


def test_registry_provides_a_default_profile() -> None:
    registry = StyleProfileRegistry()
    profile = registry.get_default()
    assert profile.id == "default"


def test_registry_registers_a_new_firm_profile() -> None:
    registry = StyleProfileRegistry()
    profile = StyleProfile(id="cabinet-x", firm_name="Cabinet X", tone="assertive")
    registry.register(profile)
    assert registry.get("cabinet-x") is profile


def test_registry_get_returns_none_for_unknown_profile() -> None:
    registry = StyleProfileRegistry()
    assert registry.get("does-not-exist") is None


def test_prompt_instructions_mention_all_four_dimensions() -> None:
    profile = StyleProfile(
        id="p", firm_name="F", tone="assertive", detail_level="detailed",
        length="long", register="direct",
    )
    instructions = StyleEngine().prompt_instructions(profile)
    assert "assertive" in instructions
    assert "detailed" in instructions
    assert "long" in instructions
    assert "direct" in instructions


def test_closing_formula_depends_on_tone() -> None:
    engine = StyleEngine()
    formal = engine.closing_formula(StyleProfile(id="p", firm_name="F", tone="formal"))
    neutral = engine.closing_formula(StyleProfile(id="p", firm_name="F", tone="neutral"))
    assert formal != neutral


def test_apply_does_not_alter_the_paragraph_substance() -> None:
    engine = StyleEngine()
    profile = StyleProfile(id="p", firm_name="F")
    text = "Le contrat est résilié."
    assert engine.apply(text, profile) == text
