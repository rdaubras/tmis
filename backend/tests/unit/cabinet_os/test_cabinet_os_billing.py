import pytest

from tmis.cabinet_os.billing.engine import BillingEngine
from tmis.cabinet_os.billing.gateway import ManualPaymentGateway, NoOpAccountingExport
from tmis.cabinet_os.billing.schemas import InvoiceStatus, PaymentMethod, QuoteStatus
from tmis.cabinet_os.billing.store import (
    InMemoryCreditNoteStore,
    InMemoryInvoiceStore,
    InMemoryPaymentStore,
    InMemoryQuoteStore,
)


def _engine() -> BillingEngine:
    return BillingEngine(
        InMemoryQuoteStore(),
        InMemoryInvoiceStore(),
        InMemoryCreditNoteStore(),
        InMemoryPaymentStore(),
        ManualPaymentGateway(),
        NoOpAccountingExport(),
    )


def test_line_item_total_applies_its_own_discount() -> None:
    engine = _engine()
    quote = engine.create_quote("firm-1", "client-1")
    engine.add_quote_line(quote.id, "Consultation", 2, 100.0, discount_percent=10.0)

    assert quote.line_items[0].total == 180.0


def test_quote_lifecycle_send_accept_convert() -> None:
    engine = _engine()
    quote = engine.create_quote("firm-1", "client-1")
    engine.add_quote_line(quote.id, "Consultation", 1, 500.0)
    engine.send_quote(quote.id)

    assert quote.status is QuoteStatus.SENT

    engine.accept_quote(quote.id)
    assert quote.status is QuoteStatus.ACCEPTED

    invoice = engine.convert_quote_to_invoice(quote.id)
    assert invoice.quote_id == quote.id
    assert invoice.status is InvoiceStatus.SENT
    assert invoice.line_items[0].description == "Consultation"


def test_cannot_convert_a_quote_that_is_not_accepted() -> None:
    engine = _engine()
    quote = engine.create_quote("firm-1", "client-1")

    with pytest.raises(ValueError, match="must be accepted"):
        engine.convert_quote_to_invoice(quote.id)


def test_issue_invoice_sets_default_due_date_30_days() -> None:
    engine = _engine()
    invoice = engine.create_invoice("firm-1", "client-1")
    engine.add_invoice_line(invoice.id, "Honoraires", 1, 1000.0)

    issued = engine.issue_invoice(invoice.id)

    assert issued.status is InvoiceStatus.SENT
    assert issued.due_at is not None
    assert issued.issued_at is not None


def test_record_full_payment_marks_invoice_paid() -> None:
    engine = _engine()
    invoice = engine.create_invoice("firm-1", "client-1")
    engine.add_invoice_line(invoice.id, "Honoraires", 1, 1000.0)
    engine.issue_invoice(invoice.id)

    engine.record_payment(invoice.id, 1000.0, PaymentMethod.BANK_TRANSFER)

    assert invoice.status is InvoiceStatus.PAID
    assert engine.total_due(invoice.id) == 0.0


def test_record_partial_payment_marks_invoice_partially_paid() -> None:
    engine = _engine()
    invoice = engine.create_invoice("firm-1", "client-1")
    engine.add_invoice_line(invoice.id, "Honoraires", 1, 1000.0)
    engine.issue_invoice(invoice.id)

    engine.record_payment(invoice.id, 400.0, PaymentMethod.CARD)

    assert invoice.status is InvoiceStatus.PARTIALLY_PAID
    assert engine.total_due(invoice.id) == 600.0


def test_manual_payment_gateway_records_what_would_be_charged() -> None:
    gateway = ManualPaymentGateway()
    engine = BillingEngine(
        InMemoryQuoteStore(),
        InMemoryInvoiceStore(),
        InMemoryCreditNoteStore(),
        InMemoryPaymentStore(),
        gateway,
        NoOpAccountingExport(),
    )
    invoice = engine.create_invoice("firm-1", "client-1")
    engine.add_invoice_line(invoice.id, "Honoraires", 1, 500.0)
    engine.issue_invoice(invoice.id)

    engine.record_payment(invoice.id, 500.0, PaymentMethod.CHECK, reference="CHK-1")

    assert gateway.recorded == [(invoice.id, 500.0, PaymentMethod.CHECK, "CHK-1")]


def test_issue_invoice_triggers_accounting_export() -> None:
    accounting = NoOpAccountingExport()
    engine = BillingEngine(
        InMemoryQuoteStore(),
        InMemoryInvoiceStore(),
        InMemoryCreditNoteStore(),
        InMemoryPaymentStore(),
        ManualPaymentGateway(),
        accounting,
    )
    invoice = engine.create_invoice("firm-1", "client-1")
    engine.add_invoice_line(invoice.id, "Honoraires", 1, 500.0)

    engine.issue_invoice(invoice.id)

    assert accounting.exported == [invoice]


def test_credit_note_reduces_total_due() -> None:
    engine = _engine()
    invoice = engine.create_invoice("firm-1", "client-1")
    engine.add_invoice_line(invoice.id, "Honoraires", 1, 1000.0)
    engine.issue_invoice(invoice.id)

    engine.issue_credit_note(invoice.id, 200.0, "Geste commercial")

    assert engine.total_due(invoice.id) == 800.0


def test_global_discount_applies_after_line_totals() -> None:
    engine = _engine()
    invoice = engine.create_invoice("firm-1", "client-1")
    engine.add_invoice_line(invoice.id, "Honoraires", 2, 100.0)
    invoice.global_discount_percent = 10.0
    engine.issue_invoice(invoice.id)

    assert engine.total_due(invoice.id) == 180.0


def test_unknown_invoice_raises() -> None:
    engine = _engine()
    with pytest.raises(ValueError, match="Unknown invoice"):
        engine.total_due("nope")


def test_unknown_quote_raises() -> None:
    engine = _engine()
    with pytest.raises(ValueError, match="Unknown quote"):
        engine.add_quote_line("nope", "x", 1, 1.0)
