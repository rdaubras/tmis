from tmis.cloud_operations.runbooks.library import DEFAULT_RUNBOOKS
from tmis.cloud_operations.runbooks.schemas import Runbook


class RunbooksEngine:
    """Read-only registry over the operational-procedure library —
    seeded with `library.DEFAULT_RUNBOOKS` but extensible via
    `register` for firm- or deployment-specific procedures."""

    def __init__(self, runbooks: tuple[Runbook, ...] = DEFAULT_RUNBOOKS) -> None:
        self._runbooks: dict[str, Runbook] = {r.slug: r for r in runbooks}

    def register(self, runbook: Runbook) -> None:
        self._runbooks[runbook.slug] = runbook

    def get(self, slug: str) -> Runbook | None:
        return self._runbooks.get(slug)

    def list_all(self) -> list[Runbook]:
        return list(self._runbooks.values())

    def find_by_tag(self, tag: str) -> list[Runbook]:
        return [r for r in self._runbooks.values() if tag in r.tags]
