from datetime import UTC, datetime

from tmis.cabinet_os.settings.ports import SettingsStorePort
from tmis.cabinet_os.settings.schemas import SettingEntry, SettingsCategory


class SettingsEngine:
    """Implements `SettingsEnginePort` (see docs/39-cabinet-os.md —
    Settings Engine): a centralized, category-scoped key/value store
    covering cabinet, users, AI, notifications, security, integrations
    and billing settings."""

    def __init__(self, store: SettingsStorePort) -> None:
        self._store = store

    def get(
        self, firm_id: str, category: SettingsCategory, key: str, default: str | None = None
    ) -> str | None:
        entry = self._store.get(firm_id, category, key)
        return entry.value if entry is not None else default

    def set(self, firm_id: str, category: SettingsCategory, key: str, value: str) -> SettingEntry:
        entry = SettingEntry(
            firm_id=firm_id,
            category=category,
            key=key,
            value=value,
            updated_at=datetime.now(UTC),
        )
        self._store.save(entry)
        return entry

    def list_category(self, firm_id: str, category: SettingsCategory) -> list[SettingEntry]:
        return self._store.list_category(firm_id, category)

    def list_all(self, firm_id: str) -> list[SettingEntry]:
        return self._store.list_all(firm_id)
