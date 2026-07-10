from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AccessAction(str, Enum):
    READ = "read"
    EXPORT = "export"
    DELETE = "delete"


@dataclass(frozen=True, slots=True)
class DataExportBundle:
    """Everything collected about one data subject across every
    registered source (see docs/48-guide-conformite.md — Export des
    données). `sections` maps a source name (e.g. `"clients"`,
    `"documents"`, `"time_entries"`) to the rows that source
    collected — the compliance engine never knows the shape of any
    business entity, only that a source produced rows."""

    firm_id: str
    subject_id: str
    sections: dict[str, list[dict[str, str]]]
    exported_at: datetime


@dataclass(frozen=True, slots=True)
class DataDeletionReceipt:
    """Proof that every registered source was asked to erase a
    subject's data, and whether each one reported success."""

    firm_id: str
    subject_id: str
    deleted_from: list[str]
    failed_sources: list[str]
    deleted_at: datetime


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    """How long an entity type may be kept before it is eligible for
    deletion (see docs/48-guide-conformite.md — Durées de
    conservation)."""

    entity_type: str
    retention_days: int


@dataclass(frozen=True, slots=True)
class AccessLogEntry:
    """One access to personal data — read, export, or delete (see
    docs/48-guide-conformite.md — Journalisation des accès).
    Append-only, distinct from `tmis.collaboration.audit.AuditEntry`:
    this log is scoped specifically to personal-data access for
    compliance reporting, not general business-action history."""

    id: str
    firm_id: str
    actor_id: str
    subject_id: str
    action: AccessAction
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class ProcessingRegisterEntry:
    """One entry in the "registre des traitements" (see
    docs/48-guide-conformite.md — Registre des traitements) — the
    record of processing activities a data controller must maintain.
    Configurable: a firm/DPO adds entries, TMIS does not hardcode a
    fixed list of processing activities."""

    id: str
    name: str
    purpose: str
    data_categories: list[str]
    legal_basis: str
    retention_policy_ref: str
    recipients: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ConsentRecord:
    """A subject's consent for one purpose — kept even after
    revocation (never deleted), so the firm can prove what consent
    state applied at any point in time (see
    docs/48-guide-conformite.md — Consentements)."""

    subject_id: str
    purpose: str
    granted: bool
    recorded_at: datetime
