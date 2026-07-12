from tmis.cabinet_os.billing.engine import BillingEngine
from tmis.cabinet_os.billing.schemas import Payment, PaymentMethod


class PaymentEngine:
    """Records payments against an invoice — composes
    `cabinet_os.billing.BillingEngine.record_payment` directly, which
    is already behind `PaymentGatewayPort` (Sprint 9): this module
    never talks to a payment provider itself, so the SaaS Business
    Platform stays "indépendant d'un prestataire de paiement" (sprint
    requirement) exactly like the engine it composes."""

    def __init__(self, billing: BillingEngine) -> None:
        self._billing = billing

    def record_payment(
        self, invoice_id: str, amount: float, method: PaymentMethod, reference: str = ""
    ) -> Payment:
        return self._billing.record_payment(invoice_id, amount, method, reference)

    def total_due(self, invoice_id: str) -> float:
        return self._billing.total_due(invoice_id)
