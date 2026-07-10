from typing import Protocol

from tmis.platform.compliance.schemas import (
    AccessAction,
    AccessLogEntry,
    ConsentRecord,
    DataDeletionReceipt,
    DataExportBundle,
    ProcessingRegisterEntry,
    RetentionPolicy,
)


class DataSourceCollectorPort(Protocol):
    """Implemented by every business module willing to participate in
    data export/deletion — one collector per source (e.g. `clients`,
    `documents`, `time_entries`). The compliance engine composes
    whichever collectors are registered; it never queries a business
    store directly (see docs/48-guide-conformite.md)."""

    def collect(self, firm_id: str, subject_id: str) -> list[dict[str, str]]: ...

    def delete(self, firm_id: str, subject_id: str) -> bool: ...


class AccessLogStorePort(Protocol):
    def save(self, entry: AccessLogEntry) -> None: ...

    def list_for_subject(self, firm_id: str, subject_id: str) -> list[AccessLogEntry]: ...


class RetentionPolicyStorePort(Protocol):
    def get(self, entity_type: str) -> RetentionPolicy | None: ...

    def save(self, policy: RetentionPolicy) -> None: ...

    def list_all(self) -> list[RetentionPolicy]: ...


class ProcessingRegisterStorePort(Protocol):
    def save(self, entry: ProcessingRegisterEntry) -> None: ...

    def list_all(self) -> list[ProcessingRegisterEntry]: ...


class ConsentStorePort(Protocol):
    def save(self, record: ConsentRecord) -> None: ...

    def list_for_subject(self, subject_id: str) -> list[ConsentRecord]: ...


class ComplianceEnginePort(Protocol):
    """Port implemented by every interchangeable compliance engine."""

    def register_source(self, name: str, collector: DataSourceCollectorPort) -> None: ...

    def export_subject_data(self, firm_id: str, subject_id: str) -> DataExportBundle: ...

    def delete_subject_data(self, firm_id: str, subject_id: str) -> DataDeletionReceipt: ...

    def log_access(
        self, firm_id: str, actor_id: str, subject_id: str, action: AccessAction
    ) -> AccessLogEntry: ...

    def access_log_for_subject(self, firm_id: str, subject_id: str) -> list[AccessLogEntry]: ...

    def set_retention_policy(self, entity_type: str, retention_days: int) -> RetentionPolicy: ...

    def is_past_retention(self, entity_type: str, age_days: int) -> bool: ...

    def register_processing_activity(
        self,
        entry_id: str,
        name: str,
        purpose: str,
        data_categories: list[str],
        legal_basis: str,
        retention_policy_ref: str,
        recipients: list[str] | None = None,
    ) -> ProcessingRegisterEntry: ...

    def list_processing_register(self) -> list[ProcessingRegisterEntry]: ...

    def grant_consent(self, subject_id: str, purpose: str) -> ConsentRecord: ...

    def revoke_consent(self, subject_id: str, purpose: str) -> ConsentRecord: ...

    def has_consent(self, subject_id: str, purpose: str) -> bool: ...
