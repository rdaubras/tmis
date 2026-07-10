from tmis.legal_drafting.validation.schemas import DraftDecision
from tmis.legal_drafting.validation.service import HumanInTheLoopService


def test_record_returns_a_validation_record() -> None:
    service = HumanInTheLoopService()
    record = service.record("doc1", DraftDecision.APPROVED, "avocat@cabinet.fr")
    assert record.document_id == "doc1"
    assert record.decision == DraftDecision.APPROVED


def test_list_for_document_returns_every_record_in_order() -> None:
    service = HumanInTheLoopService()
    service.record("doc1", DraftDecision.COMMENTED, "avocat", comment="À revoir")
    service.record("doc1", DraftDecision.APPROVED, "avocat")

    records = service.list_for_document("doc1")

    assert len(records) == 2
    assert records[0].decision == DraftDecision.COMMENTED
    assert records[1].decision == DraftDecision.APPROVED


def test_list_for_document_is_empty_for_unknown_document() -> None:
    assert HumanInTheLoopService().list_for_document("unknown") == []


def test_records_never_overwrite_each_other() -> None:
    service = HumanInTheLoopService()
    service.record("doc1", DraftDecision.REJECTED, "avocat", comment="Manque de preuves")
    service.record("doc1", DraftDecision.APPROVED, "avocat", comment="Corrigé")

    records = service.list_for_document("doc1")

    assert len(records) == 2
    assert records[0].comment == "Manque de preuves"
