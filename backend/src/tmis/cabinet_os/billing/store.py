from tmis.cabinet_os.billing.schemas import CreditNote, Invoice, Payment, Quote


class InMemoryQuoteStore:
    def __init__(self) -> None:
        self._quotes: dict[str, Quote] = {}

    def get(self, quote_id: str) -> Quote | None:
        return self._quotes.get(quote_id)

    def save(self, quote: Quote) -> None:
        self._quotes[quote.id] = quote

    def list_for_firm(self, firm_id: str) -> list[Quote]:
        return [q for q in self._quotes.values() if q.firm_id == firm_id]


class InMemoryInvoiceStore:
    def __init__(self) -> None:
        self._invoices: dict[str, Invoice] = {}

    def get(self, invoice_id: str) -> Invoice | None:
        return self._invoices.get(invoice_id)

    def save(self, invoice: Invoice) -> None:
        self._invoices[invoice.id] = invoice

    def list_for_firm(self, firm_id: str) -> list[Invoice]:
        return [i for i in self._invoices.values() if i.firm_id == firm_id]

    def list_for_client(self, client_id: str) -> list[Invoice]:
        return [i for i in self._invoices.values() if i.client_id == client_id]


class InMemoryCreditNoteStore:
    def __init__(self) -> None:
        self._credit_notes: list[CreditNote] = []

    def save(self, credit_note: CreditNote) -> None:
        self._credit_notes.append(credit_note)

    def list_for_invoice(self, invoice_id: str) -> list[CreditNote]:
        return [c for c in self._credit_notes if c.invoice_id == invoice_id]


class InMemoryPaymentStore:
    def __init__(self) -> None:
        self._payments: list[Payment] = []

    def save(self, payment: Payment) -> None:
        self._payments.append(payment)

    def list_for_invoice(self, invoice_id: str) -> list[Payment]:
        return [p for p in self._payments if p.invoice_id == invoice_id]

    def list_for_firm(self, firm_id: str) -> list[Payment]:
        return [p for p in self._payments if p.firm_id == firm_id]
