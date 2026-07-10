from datetime import datetime
from typing import Protocol

from tmis.cabinet_os.billing.schemas import (
    CreditNote,
    FeeType,
    Invoice,
    Payment,
    PaymentMethod,
    Quote,
)


class QuoteStorePort(Protocol):
    def get(self, quote_id: str) -> Quote | None: ...

    def save(self, quote: Quote) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[Quote]: ...


class InvoiceStorePort(Protocol):
    def get(self, invoice_id: str) -> Invoice | None: ...

    def save(self, invoice: Invoice) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[Invoice]: ...

    def list_for_client(self, client_id: str) -> list[Invoice]: ...


class CreditNoteStorePort(Protocol):
    def save(self, credit_note: CreditNote) -> None: ...

    def list_for_invoice(self, invoice_id: str) -> list[CreditNote]: ...


class PaymentStorePort(Protocol):
    def save(self, payment: Payment) -> None: ...

    def list_for_invoice(self, invoice_id: str) -> list[Payment]: ...

    def list_for_firm(self, firm_id: str) -> list[Payment]: ...


class PaymentGatewayPort(Protocol):
    """Extension point for a real payment provider (Stripe, GoCardless,
    ...) — see docs/42-guide-facturation.md. The reference
    implementation shipped this sprint (`ManualPaymentGateway`) only
    records what would be charged/collected, exactly like
    `tmis.collaboration.notifications.channels.EmailChannel`."""

    def record_payment(
        self, invoice_id: str, amount: float, method: PaymentMethod, reference: str
    ) -> None: ...


class AccountingExportPort(Protocol):
    """Extension point for a real accounting tool (Sage, QuickBooks,
    Pennylane...) — the reference implementation only records what
    would be exported."""

    def export_invoice(self, invoice: Invoice) -> None: ...


class BillingEnginePort(Protocol):
    """Port implemented by every interchangeable billing engine."""

    def create_quote(
        self, firm_id: str, client_id: str, case_id: str | None = None
    ) -> Quote: ...

    def add_quote_line(
        self,
        quote_id: str,
        description: str,
        quantity: float,
        unit_price: float,
        *,
        fee_type: FeeType = FeeType.HOURLY,
        discount_percent: float = 0.0,
    ) -> Quote: ...

    def send_quote(self, quote_id: str) -> Quote: ...

    def accept_quote(self, quote_id: str) -> Quote: ...

    def convert_quote_to_invoice(
        self, quote_id: str, due_at: datetime | None = None
    ) -> Invoice: ...

    def create_invoice(
        self, firm_id: str, client_id: str, case_id: str | None = None
    ) -> Invoice: ...

    def add_invoice_line(
        self,
        invoice_id: str,
        description: str,
        quantity: float,
        unit_price: float,
        *,
        fee_type: FeeType = FeeType.HOURLY,
        discount_percent: float = 0.0,
    ) -> Invoice: ...

    def issue_invoice(self, invoice_id: str, due_at: datetime | None = None) -> Invoice: ...

    def record_payment(
        self, invoice_id: str, amount: float, method: PaymentMethod, reference: str = ""
    ) -> Payment: ...

    def issue_credit_note(self, invoice_id: str, amount: float, reason: str) -> CreditNote: ...

    def total_due(self, invoice_id: str) -> float: ...

    def get_invoice(self, invoice_id: str) -> Invoice: ...
