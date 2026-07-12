from tmis.identity_platform.compliance.collectors import (
    DelegationDataCollector,
    DeviceDataCollector,
    SessionDataCollector,
    UserDataCollector,
)
from tmis.identity_platform.delegation.engine import DelegationEngine
from tmis.identity_platform.device_trust.engine import DeviceTrustEngine
from tmis.identity_platform.session_manager.engine import SessionManager
from tmis.identity_platform.users.engine import UserEngine
from tmis.platform.compliance.engine import ComplianceEngine
from tmis.platform.compliance.schemas import DataDeletionReceipt, DataExportBundle


class IdentityComplianceEngine:
    """Registers `identity_platform`'s own data (users, sessions,
    devices, delegations) as GDPR sources with the existing
    `platform.compliance.ComplianceEngine` (Sprint 10) — "conformité"
    is composed, not reimplemented (sprint requirement)."""

    def __init__(
        self,
        compliance: ComplianceEngine,
        users: UserEngine,
        sessions: SessionManager,
        devices: DeviceTrustEngine,
        delegations: DelegationEngine,
    ) -> None:
        self._compliance = compliance
        compliance.register_source("identity_users", UserDataCollector(users))
        compliance.register_source("identity_sessions", SessionDataCollector(sessions))
        compliance.register_source("identity_devices", DeviceDataCollector(devices))
        compliance.register_source("identity_delegations", DelegationDataCollector(delegations))

    def export_subject_data(self, firm_id: str, subject_id: str) -> DataExportBundle:
        return self._compliance.export_subject_data(firm_id, subject_id)

    def delete_subject_data(self, firm_id: str, subject_id: str) -> DataDeletionReceipt:
        return self._compliance.delete_subject_data(firm_id, subject_id)
