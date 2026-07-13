from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.legal_drafting.templates.schemas import DocumentType


@dataclass(frozen=True, slots=True)
class DocumentPack:
    """Composes two existing template systems rather than a third:
    `document_types` points at `legal_drafting.templates.
    DocumentTemplate` (Sprint 7, the structural truth — sections,
    variables, rules, controls) and `cabinet_template_ids` points at
    `cabinet_knowledge.templates.CabinetTemplate` (Sprint 12, a firm's
    own governed customization of one of those types)."""

    id: str
    name: str
    domain: LegalDomain
    version: int
    document_types: tuple[DocumentType, ...] = ()
    cabinet_template_ids: tuple[str, ...] = ()
    validations: tuple[str, ...] = ()
    quality_controls: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
