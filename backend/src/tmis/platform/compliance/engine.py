import uuid
from datetime import UTC, datetime

from tmis.platform.compliance.ports import (
    AccessLogStorePort,
    ConsentStorePort,
    DataSourceCollectorPort,
    ProcessingRegisterStorePort,
    RetentionPolicyStorePort,
)
from tmis.platform.compliance.schemas import (
    AccessAction,
    AccessLogEntry,
    ConsentRecord,
    DataDeletionReceipt,
    DataExportBundle,
    ProcessingRegisterEntry,
    RetentionPolicy,
)


class ComplianceEngine:
    """Implements `ComplianceEnginePort` (see docs/48-guide-conformite.md).
    Composes whichever `DataSourceCollectorPort`s are registered — it
    never imports a business module directly, so `cabinet_os`/
    `collaboration` register their own collectors at bootstrap time
    rather than this engine depending on them."""

    def __init__(
        self,
        access_log_store: AccessLogStorePort,
        retention_store: RetentionPolicyStorePort,
        processing_register_store: ProcessingRegisterStorePort,
        consent_store: ConsentStorePort,
    ) -> None:
        self._access_log = access_log_store
        self._retention = retention_store
        self._processing_register = processing_register_store
        self._consent = consent_store
        self._sources: dict[str, DataSourceCollectorPort] = {}

    def register_source(self, name: str, collector: DataSourceCollectorPort) -> None:
        self._sources[name] = collector

    def export_subject_data(self, firm_id: str, subject_id: str) -> DataExportBundle:
        sections = {
            name: collector.collect(firm_id, subject_id)
            for name, collector in self._sources.items()
        }
        return DataExportBundle(
            firm_id=firm_id,
            subject_id=subject_id,
            sections=sections,
            exported_at=datetime.now(UTC),
        )

    def delete_subject_data(self, firm_id: str, subject_id: str) -> DataDeletionReceipt:
        deleted_from: list[str] = []
        failed_sources: list[str] = []
        for name, collector in self._sources.items():
            if collector.delete(firm_id, subject_id):
                deleted_from.append(name)
            else:
                failed_sources.append(name)
        return DataDeletionReceipt(
            firm_id=firm_id,
            subject_id=subject_id,
            deleted_from=deleted_from,
            failed_sources=failed_sources,
            deleted_at=datetime.now(UTC),
        )

    def log_access(
        self, firm_id: str, actor_id: str, subject_id: str, action: AccessAction
    ) -> AccessLogEntry:
        entry = AccessLogEntry(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            actor_id=actor_id,
            subject_id=subject_id,
            action=action,
            occurred_at=datetime.now(UTC),
        )
        self._access_log.save(entry)
        return entry

    def access_log_for_subject(self, firm_id: str, subject_id: str) -> list[AccessLogEntry]:
        return self._access_log.list_for_subject(firm_id, subject_id)

    def set_retention_policy(self, entity_type: str, retention_days: int) -> RetentionPolicy:
        policy = RetentionPolicy(entity_type=entity_type, retention_days=retention_days)
        self._retention.save(policy)
        return policy

    def is_past_retention(self, entity_type: str, age_days: int) -> bool:
        """No registered policy means "keep indefinitely" — explicit
        and conservative, never guessed."""
        policy = self._retention.get(entity_type)
        if policy is None:
            return False
        return age_days > policy.retention_days

    def register_processing_activity(
        self,
        entry_id: str,
        name: str,
        purpose: str,
        data_categories: list[str],
        legal_basis: str,
        retention_policy_ref: str,
        recipients: list[str] | None = None,
    ) -> ProcessingRegisterEntry:
        entry = ProcessingRegisterEntry(
            id=entry_id,
            name=name,
            purpose=purpose,
            data_categories=data_categories,
            legal_basis=legal_basis,
            retention_policy_ref=retention_policy_ref,
            recipients=list(recipients or []),
        )
        self._processing_register.save(entry)
        return entry

    def list_processing_register(self) -> list[ProcessingRegisterEntry]:
        return self._processing_register.list_all()

    def grant_consent(self, subject_id: str, purpose: str) -> ConsentRecord:
        record = ConsentRecord(
            subject_id=subject_id, purpose=purpose, granted=True, recorded_at=datetime.now(UTC)
        )
        self._consent.save(record)
        return record

    def revoke_consent(self, subject_id: str, purpose: str) -> ConsentRecord:
        record = ConsentRecord(
            subject_id=subject_id, purpose=purpose, granted=False, recorded_at=datetime.now(UTC)
        )
        self._consent.save(record)
        return record

    def has_consent(self, subject_id: str, purpose: str) -> bool:
        records = [r for r in self._consent.list_for_subject(subject_id) if r.purpose == purpose]
        if not records:
            return False
        latest = max(records, key=lambda r: r.recorded_at)
        return latest.granted
