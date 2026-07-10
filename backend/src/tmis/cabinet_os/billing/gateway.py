from tmis.cabinet_os.billing.schemas import Invoice, PaymentMethod


class ManualPaymentGateway:
    """Implements `PaymentGatewayPort` as an interface/stub (see
    docs/42-guide-facturation.md): records what would be charged
    through a real payment provider, without processing anything —
    same pattern as
    `tmis.collaboration.notifications.channels.EmailChannel`."""

    def __init__(self) -> None:
        self.recorded: list[tuple[str, float, PaymentMethod, str]] = []

    def record_payment(
        self, invoice_id: str, amount: float, method: PaymentMethod, reference: str
    ) -> None:
        self.recorded.append((invoice_id, amount, method, reference))


class NoOpAccountingExport:
    """Implements `AccountingExportPort` as an interface/stub: records
    what would be exported to a real accounting tool."""

    def __init__(self) -> None:
        self.exported: list[Invoice] = []

    def export_invoice(self, invoice: Invoice) -> None:
        self.exported.append(invoice)
