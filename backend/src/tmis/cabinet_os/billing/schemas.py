from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FeeType(str, Enum):
    HOURLY = "hourly"
    FLAT_FEE = "flat_fee"
    SUCCESS_FEE = "success_fee"
    OTHER = "other"


class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    CHECK = "check"
    CASH = "cash"
    OTHER = "other"


@dataclass(slots=True)
class LineItem:
    """One billable line — an hourly rate, a flat fee, or any other fee
    type (see docs/42-guide-facturation.md). `total` is always
    recomputed from quantity/unit_price/discount, never stored
    separately, so it can never drift out of sync."""

    id: str
    description: str
    quantity: float
    unit_price: float
    fee_type: FeeType = FeeType.HOURLY
    discount_percent: float = 0.0

    @property
    def total(self) -> float:
        gross = self.quantity * self.unit_price
        return gross * (1 - self.discount_percent / 100)


@dataclass(slots=True)
class Quote:
    """A devis (see docs/42-guide-facturation.md — Billing Engine)."""

    id: str
    firm_id: str
    client_id: str
    case_id: str | None
    status: QuoteStatus = QuoteStatus.DRAFT
    line_items: list[LineItem] = field(default_factory=list)
    global_discount_percent: float = 0.0
    currency: str = "EUR"
    valid_until: datetime | None = None
    accepted_at: datetime | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class Invoice:
    """A facture, optionally converted from an accepted `Quote`."""

    id: str
    firm_id: str
    client_id: str
    case_id: str | None
    quote_id: str | None = None
    status: InvoiceStatus = InvoiceStatus.DRAFT
    line_items: list[LineItem] = field(default_factory=list)
    global_discount_percent: float = 0.0
    currency: str = "EUR"
    issued_at: datetime | None = None
    due_at: datetime | None = None
    credit_note_ids: set[str] = field(default_factory=set)
    payment_ids: set[str] = field(default_factory=set)
    created_at: datetime | None = None


@dataclass(slots=True)
class CreditNote:
    """An avoir issued against an invoice."""

    id: str
    firm_id: str
    invoice_id: str
    amount: float
    reason: str
    created_at: datetime | None = None


@dataclass(slots=True)
class Payment:
    """A payment recorded against an invoice — recorded through
    `PaymentGatewayPort`, which is an interface today (see
    docs/42-guide-facturation.md) pending a real payment-provider
    integration."""

    id: str
    firm_id: str
    invoice_id: str
    amount: float
    method: PaymentMethod
    reference: str = ""
    paid_at: datetime | None = None
    created_at: datetime | None = None
