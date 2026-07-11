from tmis.ai_fabric.capabilities.schemas import Capability
from tmis.ai_fabric.model_profiles.schemas import ModelProfile
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor


class InMemoryModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, ModelDescriptor] = {}

    def register(self, descriptor: ModelDescriptor) -> None:
        self._models[descriptor.name] = descriptor

    def get(self, name: str) -> ModelDescriptor | None:
        return self._models.get(name)

    def list_all(self) -> list[ModelDescriptor]:
        return list(self._models.values())

    def list_by_capability(self, capability: Capability) -> list[ModelDescriptor]:
        return [m for m in self._models.values() if capability in m.capabilities]

    def list_by_profile(self, profile: ModelProfile) -> list[ModelDescriptor]:
        return [m for m in self._models.values() if profile in m.profiles]

    def set_availability(self, name: str, available: bool) -> None:
        model = self._models.get(name)
        if model is not None:
            model.availability = available
