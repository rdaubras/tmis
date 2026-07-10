from typing import Protocol

from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.versioning.schemas import DocumentVersion, VersionDiff


class VersioningPort(Protocol):
    """Port implemented by every interchangeable versioning service."""

    def snapshot(
        self, document_id: str, sections: list[Section], author: str
    ) -> DocumentVersion: ...

    def list_versions(self, document_id: str) -> list[DocumentVersion]: ...

    def get(self, document_id: str, version_number: int) -> DocumentVersion | None: ...

    def compare(
        self, document_id: str, version_a: int, version_b: int
    ) -> VersionDiff: ...

    def restore(self, document_id: str, version_number: int) -> list[Section]: ...
