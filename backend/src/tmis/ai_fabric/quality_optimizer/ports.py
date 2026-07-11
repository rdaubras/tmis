from typing import Protocol

from tmis.ai_fabric.quality_optimizer.schemas import ModelQualityStats


class QualityStatsStorePort(Protocol):
    def get_or_create(self, model_name: str) -> ModelQualityStats: ...

    def list_all(self) -> list[ModelQualityStats]: ...
