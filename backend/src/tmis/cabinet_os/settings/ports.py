from typing import Protocol

from tmis.cabinet_os.settings.schemas import SettingEntry, SettingsCategory


class SettingsStorePort(Protocol):
    def get(self, firm_id: str, category: SettingsCategory, key: str) -> SettingEntry | None: ...

    def save(self, entry: SettingEntry) -> None: ...

    def list_category(
        self, firm_id: str, category: SettingsCategory
    ) -> list[SettingEntry]: ...

    def list_all(self, firm_id: str) -> list[SettingEntry]: ...


class SettingsEnginePort(Protocol):
    """Port implemented by every interchangeable settings engine."""

    def get(
        self, firm_id: str, category: SettingsCategory, key: str, default: str | None = None
    ) -> str | None: ...

    def set(
        self, firm_id: str, category: SettingsCategory, key: str, value: str
    ) -> SettingEntry: ...

    def list_category(
        self, firm_id: str, category: SettingsCategory
    ) -> list[SettingEntry]: ...

    def list_all(self, firm_id: str) -> list[SettingEntry]: ...
