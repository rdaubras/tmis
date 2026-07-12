from tmis.identity_platform.delegation.engine import DelegationEngine
from tmis.identity_platform.device_trust.engine import DeviceTrustEngine
from tmis.identity_platform.device_trust.schemas import DeviceTrustLevel
from tmis.identity_platform.session_manager.engine import SessionManager
from tmis.identity_platform.users.engine import UserEngine
from tmis.identity_platform.users.schemas import UserStatus


class UserDataCollector:
    """Registers `identity_platform.users` as a GDPR data source with
    `platform.compliance.ComplianceEngine` — reused directly rather
    than reimplementing export/deletion (sprint requirement: register
    the platform's own data as sources)."""

    def __init__(self, users: UserEngine) -> None:
        self._users = users

    def collect(self, firm_id: str, subject_id: str) -> list[dict[str, str]]:
        try:
            user = self._users.get(firm_id, subject_id)
        except KeyError:
            return []
        return [
            {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "status": user.status.value,
                "team_id": user.team_id or "",
                "department_id": user.department_id or "",
            }
        ]

    def delete(self, firm_id: str, subject_id: str) -> bool:
        try:
            self._users.set_status(firm_id, subject_id, UserStatus.DEACTIVATED)
        except KeyError:
            return False
        return True


class SessionDataCollector:
    def __init__(self, sessions: SessionManager) -> None:
        self._sessions = sessions

    def collect(self, firm_id: str, subject_id: str) -> list[dict[str, str]]:
        return [
            {
                "id": s.id,
                "device_id": s.device_id or "",
                "created_at": s.created_at.isoformat(),
                "expires_at": s.expires_at.isoformat(),
                "revoked": str(s.revoked),
            }
            for s in self._sessions.list_for_user(firm_id, subject_id)
        ]

    def delete(self, firm_id: str, subject_id: str) -> bool:
        self._sessions.revoke_all_for_user(firm_id, subject_id)
        return True


class DeviceDataCollector:
    def __init__(self, devices: DeviceTrustEngine) -> None:
        self._devices = devices

    def collect(self, firm_id: str, subject_id: str) -> list[dict[str, str]]:
        return [
            {
                "id": d.id,
                "label": d.label,
                "trust_level": d.trust_level.value,
                "last_seen_at": d.last_seen_at.isoformat(),
            }
            for d in self._devices.list_for_user(firm_id, subject_id)
        ]

    def delete(self, firm_id: str, subject_id: str) -> bool:
        for device in self._devices.list_for_user(firm_id, subject_id):
            if device.trust_level is not DeviceTrustLevel.REVOKED:
                self._devices.revoke(firm_id, device.id)
        return True


class DelegationDataCollector:
    def __init__(self, delegations: DelegationEngine) -> None:
        self._delegations = delegations

    def collect(self, firm_id: str, subject_id: str) -> list[dict[str, str]]:
        return [
            {
                "id": d.id,
                "delegator_id": d.delegator_id,
                "delegate_id": d.delegate_id,
                "starts_at": d.starts_at.isoformat(),
                "ends_at": d.ends_at.isoformat(),
                "revoked": str(d.revoked),
            }
            for d in self._delegations.active_delegations_for_firm(firm_id)
            if subject_id in (d.delegator_id, d.delegate_id)
        ]

    def delete(self, firm_id: str, subject_id: str) -> bool:
        for d in self._delegations.active_delegations_for_firm(firm_id):
            if subject_id in (d.delegator_id, d.delegate_id):
                self._delegations.revoke(firm_id, d.id)
        return True
