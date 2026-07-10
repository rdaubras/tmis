import dataclasses
import uuid
from datetime import UTC, datetime

from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.versioning.schemas import DocumentVersion, VersionDiff


def _copy_paragraph(paragraph: Paragraph) -> Paragraph:
    return dataclasses.replace(paragraph)


def _copy_sections(sections: list[Section]) -> list[Section]:
    return [
        dataclasses.replace(section, paragraphs=[_copy_paragraph(p) for p in section.paragraphs])
        for section in sections
    ]


class InMemoryVersioningService:
    """Implements `VersioningPort`: every snapshot is a deep copy, so
    later regenerating a section or a paragraph on the live document
    never retroactively changes a past version (see
    docs/31-guide-versioning.md)."""

    def __init__(self) -> None:
        self._versions: dict[str, list[DocumentVersion]] = {}

    def snapshot(self, document_id: str, sections: list[Section], author: str) -> DocumentVersion:
        existing = self._versions.setdefault(document_id, [])
        version = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=document_id,
            version_number=len(existing) + 1,
            sections=tuple(_copy_sections(sections)),
            author=author,
            created_at=datetime.now(UTC),
        )
        existing.append(version)
        return version

    def list_versions(self, document_id: str) -> list[DocumentVersion]:
        return list(self._versions.get(document_id, []))

    def get(self, document_id: str, version_number: int) -> DocumentVersion | None:
        return next(
            (v for v in self._versions.get(document_id, []) if v.version_number == version_number),
            None,
        )

    def compare(self, document_id: str, version_a: int, version_b: int) -> VersionDiff:
        va = self.get(document_id, version_a)
        vb = self.get(document_id, version_b)
        if va is None or vb is None:
            raise ValueError(f"Unknown version for document {document_id!r}")

        texts_a = {p.id: p.text for s in va.sections for p in s.paragraphs}
        texts_b = {p.id: p.text for s in vb.sections for p in s.paragraphs}

        added = tuple(pid for pid in texts_b if pid not in texts_a)
        removed = tuple(pid for pid in texts_a if pid not in texts_b)
        changed = tuple(
            pid for pid in texts_a if pid in texts_b and texts_a[pid] != texts_b[pid]
        )
        return VersionDiff(
            version_a=version_a,
            version_b=version_b,
            added_paragraph_ids=added,
            removed_paragraph_ids=removed,
            changed_paragraph_ids=changed,
        )

    def restore(self, document_id: str, version_number: int) -> list[Section]:
        version = self.get(document_id, version_number)
        if version is None:
            raise ValueError(f"Unknown version {version_number} for document {document_id!r}")
        return _copy_sections(list(version.sections))
