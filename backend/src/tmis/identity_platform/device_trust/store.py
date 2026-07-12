from tmis.identity_platform.device_trust.schemas import Device


class InMemoryDeviceStore:
    def __init__(self) -> None:
        self._devices: dict[tuple[str, str], Device] = {}

    def save(self, device: Device) -> None:
        self._devices[(device.firm_id, device.id)] = device

    def get(self, firm_id: str, device_id: str) -> Device | None:
        return self._devices.get((firm_id, device_id))

    def list_for_user(self, firm_id: str, user_id: str) -> list[Device]:
        return [d for d in self._devices.values() if d.firm_id == firm_id and d.user_id == user_id]

    def list_for_firm(self, firm_id: str) -> list[Device]:
        return [d for d in self._devices.values() if d.firm_id == firm_id]
