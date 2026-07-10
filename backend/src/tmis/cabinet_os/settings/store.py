from tmis.cabinet_os.settings.schemas import SettingEntry, SettingsCategory


class InMemorySettingsStore:
    """Implements `SettingsStorePort` with an in-memory dict keyed by
    `(firm_id, category, key)` — a new value for the same key replaces
    the previous one."""

    def __init__(self) -> None:
        self._entries: dict[tuple[str, SettingsCategory, str], SettingEntry] = {}

    def get(self, firm_id: str, category: SettingsCategory, key: str) -> SettingEntry | None:
        return self._entries.get((firm_id, category, key))

    def save(self, entry: SettingEntry) -> None:
        self._entries[(entry.firm_id, entry.category, entry.key)] = entry

    def list_category(self, firm_id: str, category: SettingsCategory) -> list[SettingEntry]:
        return [
            e
            for (fid, cat, _key), e in self._entries.items()
            if fid == firm_id and cat == category
        ]

    def list_all(self, firm_id: str) -> list[SettingEntry]:
        return [e for (fid, _cat, _key), e in self._entries.items() if fid == firm_id]
