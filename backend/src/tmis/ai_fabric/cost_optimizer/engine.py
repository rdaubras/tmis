from tmis.ai_fabric.cache.engine import ResponseCache
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor


class CostOptimizer:
    """The sprint's "COST OPTIMIZER": limits unnecessary calls (via
    `tmis.ai_fabric.cache`), and routes to the cheapest model that
    still clears a minimum quality bar rather than always reaching
    for the most expensive/capable model."""

    def __init__(self, cache: ResponseCache | None = None) -> None:
        self._cache = cache

    async def try_cached_response(self, task_type: str, model_name: str, prompt: str) -> str | None:
        if self._cache is None:
            return None
        return await self._cache.get(task_type, model_name, prompt)

    def cheapest_meeting_quality(
        self, candidates: list[ModelDescriptor], min_quality_score: float
    ) -> ModelDescriptor | None:
        eligible = [
            model
            for model in candidates
            if model.availability and model.quality_score >= min_quality_score
        ]
        if not eligible:
            return None
        return min(eligible, key=lambda model: model.cost_per_1k_tokens_usd)
