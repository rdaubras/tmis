from datetime import UTC, datetime

from tmis.identity_platform.device_trust.ports import DeviceStorePort
from tmis.identity_platform.device_trust.schemas import Device, DeviceTrustLevel, new_device_id


class DeviceTrustEngine:
    """Registration, trust scoring and revocation of known devices —
    "les politiques peuvent imposer une authentification renforcée sur
    un appareil inconnu" (sprint requirement): a fresh device starts
    `UNKNOWN`, never `TRUSTED`, so `risk_engine` can require step-up
    MFA for it until explicitly trusted."""

    def __init__(self, store: DeviceStorePort) -> None:
        self._store = store

    def register(self, firm_id: str, user_id: str, label: str) -> Device:
        device = Device(id=new_device_id(), firm_id=firm_id, user_id=user_id, label=label)
        self._store.save(device)
        return device

    def trust(self, firm_id: str, device_id: str) -> Device:
        device = self._get(firm_id, device_id)
        device.trust_level = DeviceTrustLevel.TRUSTED
        self._store.save(device)
        return device

    def revoke(self, firm_id: str, device_id: str) -> Device:
        device = self._get(firm_id, device_id)
        device.trust_level = DeviceTrustLevel.REVOKED
        self._store.save(device)
        return device

    def touch(self, firm_id: str, device_id: str) -> Device:
        device = self._get(firm_id, device_id)
        device.last_seen_at = datetime.now(UTC)
        self._store.save(device)
        return device

    def is_trusted(self, firm_id: str, device_id: str) -> bool:
        device = self._store.get(firm_id, device_id)
        return device is not None and device.trust_level is DeviceTrustLevel.TRUSTED

    def list_for_user(self, firm_id: str, user_id: str) -> list[Device]:
        return self._store.list_for_user(firm_id, user_id)

    def list_for_firm(self, firm_id: str) -> list[Device]:
        return self._store.list_for_firm(firm_id)

    def _get(self, firm_id: str, device_id: str) -> Device:
        device = self._store.get(firm_id, device_id)
        if device is None:
            raise KeyError(device_id)
        return device
