import uuid
from datetime import UTC, datetime, timedelta

from tmis.cabinet_os.billing.ports import (
    AccountingExportPort,
    CreditNoteStorePort,
    InvoiceStorePort,
    PaymentGatewayPort,
    PaymentStorePort,
    QuoteStorePort,
)
from tmis.cabinet_os.billing.schemas import (
    CreditNote,
    FeeType,
    Invoice,
    InvoiceStatus,
    LineItem,
    Payment,
    PaymentMethod,
    Quote,
    QuoteStatus,
)


def _document_total(line_items: list[LineItem], global_discount_percent: float) -> float:
    subtotal = sum(item.total for item in line_items)
    return subtotal * (1 - global_discount_percent / 100)


class BillingEngine:
    """Implements `BillingEnginePort` (see docs/42-guide-facturation.md):
    quotes, invoices, credit notes and payments, with hourly rates,
    flat fees and discounts all expressed as `LineItem`s. Payment
    collection and accounting export are behind narrow ports
    (`PaymentGatewayPort`, `AccountingExportPort`) so a real provider
    can be plugged in later without touching this engine.
    """

    def __init__(
        self,
        quote_store: QuoteStorePort,
        invoice_store: InvoiceStorePort,
        credit_note_store: CreditNoteStorePort,
        payment_store: PaymentStorePort,
        payment_gateway: PaymentGatewayPort,
        accounting_export: AccountingExportPort,
    ) -> None:
        self._quotes = quote_store
        self._invoices = invoice_store
        self._credit_notes = credit_note_store
        self._payments = payment_store
        self._gateway = payment_gateway
        self._accounting = accounting_export

    def create_quote(self, firm_id: str, client_id: str, case_id: str | None = None) -> Quote:
        quote = Quote(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            client_id=client_id,
            case_id=case_id,
            created_at=datetime.now(UTC),
        )
        self._quotes.save(quote)
        return quote

    def add_quote_line(
        self,
        quote_id: str,
        description: str,
        quantity: float,
        unit_price: float,
        *,
        fee_type: FeeType = FeeType.HOURLY,
        discount_percent: float = 0.0,
    ) -> Quote:
        quote = self._require_quote(quote_id)
        quote.line_items.append(
            LineItem(
                id=str(uuid.uuid4()),
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                fee_type=fee_type,
                discount_percent=discount_percent,
            )
        )
        self._quotes.save(quote)
        return quote

    def send_quote(self, quote_id: str) -> Quote:
        quote = self._require_quote(quote_id)
        quote.status = QuoteStatus.SENT
        self._quotes.save(quote)
        return quote

    def accept_quote(self, quote_id: str) -> Quote:
        quote = self._require_quote(quote_id)
        quote.status = QuoteStatus.ACCEPTED
        quote.accepted_at = datetime.now(UTC)
        self._quotes.save(quote)
        return quote

    def convert_quote_to_invoice(
        self, quote_id: str, due_at: datetime | None = None
    ) -> Invoice:
        quote = self._require_quote(quote_id)
        if quote.status is not QuoteStatus.ACCEPTED:
            raise ValueError(f"Quote {quote_id!r} must be accepted before invoicing")
        invoice = Invoice(
            id=str(uuid.uuid4()),
            firm_id=quote.firm_id,
            client_id=quote.client_id,
            case_id=quote.case_id,
            quote_id=quote.id,
            line_items=list(quote.line_items),
            global_discount_percent=quote.global_discount_percent,
            currency=quote.currency,
            created_at=datetime.now(UTC),
        )
        self._invoices.save(invoice)
        return self.issue_invoice(invoice.id, due_at)

    def create_invoice(self, firm_id: str, client_id: str, case_id: str | None = None) -> Invoice:
        invoice = Invoice(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            client_id=client_id,
            case_id=case_id,
            created_at=datetime.now(UTC),
        )
        self._invoices.save(invoice)
        return invoice

    def add_invoice_line(
        self,
        invoice_id: str,
        description: str,
        quantity: float,
        unit_price: float,
        *,
        fee_type: FeeType = FeeType.HOURLY,
        discount_percent: float = 0.0,
    ) -> Invoice:
        invoice = self._require_invoice(invoice_id)
        invoice.line_items.append(
            LineItem(
                id=str(uuid.uuid4()),
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                fee_type=fee_type,
                discount_percent=discount_percent,
            )
        )
        self._invoices.save(invoice)
        return invoice

    def issue_invoice(self, invoice_id: str, due_at: datetime | None = None) -> Invoice:
        invoice = self._require_invoice(invoice_id)
        now = datetime.now(UTC)
        invoice.status = InvoiceStatus.SENT
        invoice.issued_at = now
        invoice.due_at = due_at or (now + timedelta(days=30))
        self._invoices.save(invoice)
        self._accounting.export_invoice(invoice)
        return invoice

    def record_payment(
        self, invoice_id: str, amount: float, method: PaymentMethod, reference: str = ""
    ) -> Payment:
        invoice = self._require_invoice(invoice_id)
        payment = Payment(
            id=str(uuid.uuid4()),
            firm_id=invoice.firm_id,
            invoice_id=invoice_id,
            amount=amount,
            method=method,
            reference=reference,
            paid_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        self._payments.save(payment)
        self._gateway.record_payment(invoice_id, amount, method, reference)
        invoice.payment_ids.add(payment.id)
        remaining = self.total_due(invoice_id)
        invoice.status = InvoiceStatus.PAID if remaining <= 0 else InvoiceStatus.PARTIALLY_PAID
        self._invoices.save(invoice)
        return payment

    def issue_credit_note(self, invoice_id: str, amount: float, reason: str) -> CreditNote:
        invoice = self._require_invoice(invoice_id)
        credit_note = CreditNote(
            id=str(uuid.uuid4()),
            firm_id=invoice.firm_id,
            invoice_id=invoice_id,
            amount=amount,
            reason=reason,
            created_at=datetime.now(UTC),
        )
        self._credit_notes.save(credit_note)
        invoice.credit_note_ids.add(credit_note.id)
        self._invoices.save(invoice)
        return credit_note

    def total_due(self, invoice_id: str) -> float:
        invoice = self._require_invoice(invoice_id)
        gross = _document_total(invoice.line_items, invoice.global_discount_percent)
        credited = sum(c.amount for c in self._credit_notes.list_for_invoice(invoice_id))
        paid = sum(p.amount for p in self._payments.list_for_invoice(invoice_id))
        return gross - credited - paid

    def get_invoice(self, invoice_id: str) -> Invoice:
        return self._require_invoice(invoice_id)

    def _require_quote(self, quote_id: str) -> Quote:
        quote = self._quotes.get(quote_id)
        if quote is None:
            raise ValueError(f"Unknown quote {quote_id!r}")
        return quote

    def _require_invoice(self, invoice_id: str) -> Invoice:
        invoice = self._invoices.get(invoice_id)
        if invoice is None:
            raise ValueError(f"Unknown invoice {invoice_id!r}")
        return invoice
