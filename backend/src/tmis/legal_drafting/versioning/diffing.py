from tmis.legal_drafting.versioning.schemas import DocumentVersion, VersionDiff


def diff_versions(version_a: DocumentVersion, version_b: DocumentVersion) -> VersionDiff:
    """Paragraph-level diff between two snapshots — shared by every
    `VersioningPort` implementation (`InMemoryVersioningService`,
    `SQLAlchemyVersioningService`) so the comparison logic exists once."""
    texts_a = {p.id: p.text for s in version_a.sections for p in s.paragraphs}
    texts_b = {p.id: p.text for s in version_b.sections for p in s.paragraphs}

    added = tuple(pid for pid in texts_b if pid not in texts_a)
    removed = tuple(pid for pid in texts_a if pid not in texts_b)
    changed = tuple(pid for pid in texts_a if pid in texts_b and texts_a[pid] != texts_b[pid])
    return VersionDiff(
        version_a=version_a.version_number,
        version_b=version_b.version_number,
        added_paragraph_ids=added,
        removed_paragraph_ids=removed,
        changed_paragraph_ids=changed,
    )
