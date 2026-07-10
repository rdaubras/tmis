from tmis.platform.compliance.engine import ComplianceEngine
from tmis.platform.compliance.schemas import AccessAction
from tmis.platform.compliance.store import (
    InMemoryAccessLogStore,
    InMemoryConsentStore,
    InMemoryProcessingRegisterStore,
    InMemoryRetentionPolicyStore,
)


class _FakeCollector:
    def __init__(self, rows: list[dict[str, str]], delete_succeeds: bool = True) -> None:
        self._rows = rows
        self._delete_succeeds = delete_succeeds
        self.deleted = False

    def collect(self, firm_id: str, subject_id: str) -> list[dict[str, str]]:
        return self._rows

    def delete(self, firm_id: str, subject_id: str) -> bool:
        self.deleted = True
        return self._delete_succeeds


def _engine() -> ComplianceEngine:
    return ComplianceEngine(
        InMemoryAccessLogStore(),
        InMemoryRetentionPolicyStore(),
        InMemoryProcessingRegisterStore(),
        InMemoryConsentStore(),
    )


def test_export_subject_data_aggregates_every_registered_source() -> None:
    engine = _engine()
    engine.register_source("clients", _FakeCollector([{"name": "Acme Corp"}]))
    engine.register_source("documents", _FakeCollector([{"title": "NDA"}]))

    bundle = engine.export_subject_data("firm-1", "client-1")

    assert bundle.sections == {"clients": [{"name": "Acme Corp"}], "documents": [{"title": "NDA"}]}


def test_delete_subject_data_reports_failed_sources_separately() -> None:
    engine = _engine()
    engine.register_source("clients", _FakeCollector([], delete_succeeds=True))
    engine.register_source("billing", _FakeCollector([], delete_succeeds=False))

    receipt = engine.delete_subject_data("firm-1", "client-1")

    assert receipt.deleted_from == ["clients"]
    assert receipt.failed_sources == ["billing"]


def test_log_access_is_retrievable_per_subject() -> None:
    engine = _engine()
    engine.log_access("firm-1", "user-1", "client-1", AccessAction.READ)
    engine.log_access("firm-1", "user-1", "client-2", AccessAction.READ)

    entries = engine.access_log_for_subject("firm-1", "client-1")

    assert len(entries) == 1
    assert entries[0].action is AccessAction.READ


def test_retention_policy_flags_records_past_their_retention_window() -> None:
    engine = _engine()
    engine.set_retention_policy("time_entries", retention_days=365)

    assert engine.is_past_retention("time_entries", age_days=400) is True
    assert engine.is_past_retention("time_entries", age_days=100) is False


def test_is_past_retention_defaults_to_keep_indefinitely_when_unconfigured() -> None:
    engine = _engine()

    assert engine.is_past_retention("unknown_entity", age_days=10_000) is False


def test_processing_register_entries_are_listable() -> None:
    engine = _engine()
    engine.register_processing_activity(
        "reg-1", "Client onboarding", "contract management", ["identity"], "contract", "clients"
    )

    entries = engine.list_processing_register()

    assert len(entries) == 1
    assert entries[0].name == "Client onboarding"


def test_consent_reflects_the_latest_grant_or_revocation() -> None:
    engine = _engine()
    engine.grant_consent("client-1", "marketing")
    engine.revoke_consent("client-1", "marketing")

    assert engine.has_consent("client-1", "marketing") is False


def test_has_consent_is_false_when_never_granted() -> None:
    engine = _engine()

    assert engine.has_consent("client-1", "marketing") is False
