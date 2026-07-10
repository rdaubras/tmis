from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RestorePlan:
    """Result of a dry-run restore — lets an operator review what a
    restore would do before committing to it (see
    docs/47-guide-securite-entreprise.md — Disaster Recovery)."""

    backup_id: str
    files: list[str] = field(default_factory=list)
    total_size_bytes: int = 0
    warnings: list[str] = field(default_factory=list)
