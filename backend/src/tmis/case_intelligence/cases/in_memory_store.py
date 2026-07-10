from tmis.case_intelligence.cases.schemas import CaseProfile


class InMemoryCaseStore:
    """Implements `CaseStorePort` with a process-local dict.

    Default backend for local development and tests; real persistence is
    planned for Sprint 6-7 (see `tmis.case_intelligence.cases` module
    docstring and docs/09-roadmap-30-sprints.md).
    """

    def __init__(self) -> None:
        self._profiles: dict[str, CaseProfile] = {}

    def get(self, case_id: str) -> CaseProfile | None:
        return self._profiles.get(case_id)

    def save(self, profile: CaseProfile) -> None:
        self._profiles[profile.case_id] = profile

    def get_or_create(self, case_id: str, title: str) -> CaseProfile:
        existing = self._profiles.get(case_id)
        if existing is not None:
            return existing
        profile = CaseProfile(case_id=case_id, title=title)
        self._profiles[case_id] = profile
        return profile

    def list_ids(self) -> list[str]:
        return list(self._profiles)
