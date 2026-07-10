from typing import Protocol

from tmis.platform.feature_flags.schemas import FeatureFlag, FlagEvaluationContext


class FeatureFlagStorePort(Protocol):
    def save(self, flag: FeatureFlag) -> None: ...

    def get(self, key: str) -> FeatureFlag | None: ...

    def list_all(self) -> list[FeatureFlag]: ...


class FeatureFlagEnginePort(Protocol):
    """Port implemented by every interchangeable feature-flag engine."""

    def is_enabled(self, key: str, context: FlagEvaluationContext) -> bool: ...

    def set_flag(self, flag: FeatureFlag) -> FeatureFlag: ...
