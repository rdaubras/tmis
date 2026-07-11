from tmis.ai_fabric.fallback.schemas import NoAvailableModelError
from tmis.ai_fabric.model_registry.ports import ModelRegistryPort
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor


class FallbackEngine:
    """The sprint's requirement that "le système doit fonctionner même
    si un fournisseur est indisponible": walks an ordered chain of
    model names — the primary, then its configured fallbacks — and
    resolves the first one that is both registered and available.
    Tracks how often a fallback (rather than the primary) was needed,
    feeding the "taux de fallback" dashboard metric
    (`tmis.ai_fabric.telemetry`)."""

    def __init__(self, model_registry: ModelRegistryPort) -> None:
        self._model_registry = model_registry
        self._total_resolutions = 0
        self._fallback_resolutions = 0

    def resolve(
        self, primary_model_name: str, fallback_model_names: tuple[str, ...] = ()
    ) -> ModelDescriptor:
        attempted = (primary_model_name, *fallback_model_names)
        self._total_resolutions += 1
        for index, name in enumerate(attempted):
            model = self._model_registry.get(name)
            if model is not None and model.availability:
                if index > 0:
                    self._fallback_resolutions += 1
                return model
        raise NoAvailableModelError(attempted)

    def fallback_rate(self) -> float:
        if self._total_resolutions == 0:
            return 0.0
        return self._fallback_resolutions / self._total_resolutions
