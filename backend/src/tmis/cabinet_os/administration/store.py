from tmis.cabinet_os.administration.schemas import ConnectorStatus, FirmRecord, GlobalConfigEntry


class InMemoryFirmRegistry:
    def __init__(self) -> None:
        self._firms: dict[str, FirmRecord] = {}

    def get(self, firm_id: str) -> FirmRecord | None:
        return self._firms.get(firm_id)

    def save(self, firm: FirmRecord) -> None:
        self._firms[firm.id] = firm

    def list_all(self) -> list[FirmRecord]:
        return list(self._firms.values())


class InMemoryConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, ConnectorStatus] = {}

    def save(self, connector: ConnectorStatus) -> None:
        self._connectors[connector.name] = connector

    def list_all(self) -> list[ConnectorStatus]:
        return list(self._connectors.values())


class InMemoryGlobalConfig:
    def __init__(self) -> None:
        self._entries: dict[str, GlobalConfigEntry] = {}

    def get(self, key: str) -> GlobalConfigEntry | None:
        return self._entries.get(key)

    def save(self, entry: GlobalConfigEntry) -> None:
        self._entries[entry.key] = entry

    def list_all(self) -> list[GlobalConfigEntry]:
        return list(self._entries.values())
