from tmis.legal_drafting.history.schemas import DraftHistoryActionType
from tmis.legal_drafting.history.store import InMemoryDraftHistory


def test_record_appends_an_entry() -> None:
    history = InMemoryDraftHistory()
    history.record("doc1", DraftHistoryActionType.CREATED, details="Généré")
    entries = history.list_for_document("doc1")
    assert len(entries) == 1
    assert entries[0].action == DraftHistoryActionType.CREATED


def test_entries_are_never_overwritten() -> None:
    history = InMemoryDraftHistory()
    history.record("doc1", DraftHistoryActionType.CREATED)
    history.record("doc1", DraftHistoryActionType.SECTION_REGENERATED, author="avocat")
    entries = history.list_for_document("doc1")
    assert [e.action for e in entries] == [
        DraftHistoryActionType.CREATED,
        DraftHistoryActionType.SECTION_REGENERATED,
    ]


def test_list_for_unknown_document_is_empty() -> None:
    assert InMemoryDraftHistory().list_for_document("unknown") == []
