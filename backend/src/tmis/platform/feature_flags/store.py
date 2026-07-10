from tmis.platform.feature_flags.schemas import FeatureFlag


class InMemoryFeatureFlagStore:
    def __init__(self) -> None:
        self._flags: dict[str, FeatureFlag] = {}

    def save(self, flag: FeatureFlag) -> None:
        self._flags[flag.key] = flag

    def get(self, key: str) -> FeatureFlag | None:
        return self._flags.get(key)

    def list_all(self) -> list[FeatureFlag]:
        return list(self._flags.values())
