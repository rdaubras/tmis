from tmis.business_platform.feature_flags.schemas import BusinessFlagExtras


class InMemoryBusinessFlagExtrasStore:
    def __init__(self) -> None:
        self._extras: dict[str, BusinessFlagExtras] = {}

    def save(self, extras: BusinessFlagExtras) -> None:
        self._extras[extras.key] = extras

    def get(self, key: str) -> BusinessFlagExtras | None:
        return self._extras.get(key)

    def list_all(self) -> list[BusinessFlagExtras]:
        return list(self._extras.values())
