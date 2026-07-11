from tmis.ai_fabric.capabilities.schemas import Capability
from tmis.ai_fabric.model_profiles.schemas import ModelProfile, default_capabilities_for_profile
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor
from tmis.ai_fabric.model_registry.store import InMemoryModelRegistry


def _descriptor(name: str, **overrides: object) -> ModelDescriptor:
    defaults: dict[str, object] = dict(
        name=name,
        version="1",
        provider="openai",
        cost_per_1k_tokens_usd=0.01,
        avg_latency_ms=500.0,
        max_context_tokens=8_000,
        capabilities=frozenset({Capability.TEXT_COMPLETION}),
        profiles=frozenset({ModelProfile.REASONING}),
    )
    defaults.update(overrides)
    return ModelDescriptor(**defaults)  # type: ignore[arg-type]


def test_default_capabilities_for_profile_is_non_empty_for_every_profile() -> None:
    for profile in ModelProfile:
        assert default_capabilities_for_profile(profile)


def test_model_registry_register_and_get() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_descriptor("gpt-x"))

    assert registry.get("gpt-x") is not None
    assert registry.get("unknown") is None


def test_model_registry_list_by_capability_and_profile() -> None:
    registry = InMemoryModelRegistry()
    registry.register(
        _descriptor(
            "vision-1",
            capabilities=frozenset({Capability.VISION}),
            profiles=frozenset({ModelProfile.VISION}),
        )
    )
    registry.register(_descriptor("reason-1"))

    assert [m.name for m in registry.list_by_capability(Capability.VISION)] == ["vision-1"]
    assert [m.name for m in registry.list_by_profile(ModelProfile.REASONING)] == ["reason-1"]


def test_model_registry_set_availability() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_descriptor("gpt-x"))

    registry.set_availability("gpt-x", False)

    model = registry.get("gpt-x")
    assert model is not None
    assert model.availability is False


def test_model_registry_set_availability_on_unknown_model_is_a_no_op() -> None:
    registry = InMemoryModelRegistry()

    registry.set_availability("unknown", False)  # must not raise
