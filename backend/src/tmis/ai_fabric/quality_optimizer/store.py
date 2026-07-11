from tmis.ai_fabric.quality_optimizer.schemas import ModelQualityStats


class InMemoryQualityStatsStore:
    def __init__(self) -> None:
        self._stats: dict[str, ModelQualityStats] = {}

    def get_or_create(self, model_name: str) -> ModelQualityStats:
        return self._stats.setdefault(model_name, ModelQualityStats(model_name=model_name))

    def list_all(self) -> list[ModelQualityStats]:
        return list(self._stats.values())
