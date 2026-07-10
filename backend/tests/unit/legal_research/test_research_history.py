from datetime import UTC, datetime

from tmis.legal_research.history.in_memory_history import InMemoryResearchHistory
from tmis.legal_research.history.schemas import ResearchHistoryEntry


def _entry(**overrides: object) -> ResearchHistoryEntry:
    defaults: dict[str, object] = dict(
        id="s1",
        query_text="licenciement",
        timestamp=datetime.now(UTC),
        connectors_used=("codes",),
        duration_ms=12.5,
        result_count=3,
        user_id="user-1",
        case_id="case-1",
    )
    defaults.update(overrides)
    return ResearchHistoryEntry(**defaults)  # type: ignore[arg-type]


def test_record_and_list_all() -> None:
    history = InMemoryResearchHistory()
    history.record(_entry())
    assert len(history.list_all()) == 1


def test_list_for_user_filters_correctly() -> None:
    history = InMemoryResearchHistory()
    history.record(_entry(id="s1", user_id="user-1"))
    history.record(_entry(id="s2", user_id="user-2"))

    entries = history.list_for_user("user-1")

    assert [e.id for e in entries] == ["s1"]


def test_list_for_case_filters_correctly() -> None:
    history = InMemoryResearchHistory()
    history.record(_entry(id="s1", case_id="case-1"))
    history.record(_entry(id="s2", case_id="case-2"))

    entries = history.list_for_case("case-2")

    assert [e.id for e in entries] == ["s2"]
