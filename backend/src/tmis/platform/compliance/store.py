from tmis.platform.compliance.schemas import (
    AccessLogEntry,
    ConsentRecord,
    ProcessingRegisterEntry,
    RetentionPolicy,
)


class InMemoryAccessLogStore:
    def __init__(self) -> None:
        self._entries: list[AccessLogEntry] = []

    def save(self, entry: AccessLogEntry) -> None:
        self._entries.append(entry)

    def list_for_subject(self, firm_id: str, subject_id: str) -> list[AccessLogEntry]:
        return [
            e for e in self._entries if e.firm_id == firm_id and e.subject_id == subject_id
        ]


class InMemoryRetentionPolicyStore:
    def __init__(self) -> None:
        self._policies: dict[str, RetentionPolicy] = {}

    def get(self, entity_type: str) -> RetentionPolicy | None:
        return self._policies.get(entity_type)

    def save(self, policy: RetentionPolicy) -> None:
        self._policies[policy.entity_type] = policy

    def list_all(self) -> list[RetentionPolicy]:
        return list(self._policies.values())


class InMemoryProcessingRegisterStore:
    def __init__(self) -> None:
        self._entries: dict[str, ProcessingRegisterEntry] = {}

    def save(self, entry: ProcessingRegisterEntry) -> None:
        self._entries[entry.id] = entry

    def list_all(self) -> list[ProcessingRegisterEntry]:
        return list(self._entries.values())


class InMemoryConsentStore:
    def __init__(self) -> None:
        self._records: list[ConsentRecord] = []

    def save(self, record: ConsentRecord) -> None:
        self._records.append(record)

    def list_for_subject(self, subject_id: str) -> list[ConsentRecord]:
        return [r for r in self._records if r.subject_id == subject_id]
