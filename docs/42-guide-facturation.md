# Guide — Facturation

## Devis, factures, avoirs, paiements

```python
from tmis.cabinet_os.billing.engine import BillingEngine
from tmis.cabinet_os.billing.schemas import FeeType, PaymentMethod

quote = billing.create_quote("firm-1", client_id)
billing.add_quote_line(quote.id, "Consultation", 2, 100.0, fee_type=FeeType.HOURLY)
billing.send_quote(quote.id)
billing.accept_quote(quote.id)
invoice = billing.convert_quote_to_invoice(quote.id)  # émet directement la facture
```

Une facture peut aussi être créée directement, sans devis :

```python
invoice = billing.create_invoice("firm-1", client_id)
billing.add_invoice_line(invoice.id, "Honoraires", 1, 1500.0, fee_type=FeeType.FLAT_FEE)
billing.issue_invoice(invoice.id)  # échéance à 30 jours par défaut
```

## Le total d'une ligne ne se stocke jamais

```python
line_item.total  # quantity * unit_price * (1 - discount_percent / 100)
```

`LineItem.total` est une propriété calculée — jamais une valeur
stockée séparément, donc jamais susceptible de désynchronisation avec
la quantité, le prix unitaire ou la remise. Une remise globale
(`Quote.global_discount_percent`/`Invoice.global_discount_percent`)
s'applique *après* la somme des lignes.

## Paiements et avoirs

```python
billing.record_payment(invoice.id, 500.0, PaymentMethod.BANK_TRANSFER, reference="VIR-042")
billing.issue_credit_note(invoice.id, 100.0, "Geste commercial")
billing.total_due(invoice.id)  # total - avoirs - paiements
```

Le statut de la facture (`SENT` → `PARTIALLY_PAID` → `PAID`) est
recalculé automatiquement à partir de `total_due` après chaque
paiement.

## Intégrations futures : deux ports, deux interfaces

```python
from tmis.cabinet_os.billing.gateway import ManualPaymentGateway, NoOpAccountingExport
```

`PaymentGatewayPort.record_payment()` et
`AccountingExportPort.export_invoice()` sont deux points d'extension.
Les implémentations livrées ce sprint (`ManualPaymentGateway`,
`NoOpAccountingExport`) sont des **interfaces** au sens du brief :
elles enregistrent ce qui serait envoyé à un vrai prestataire de
paiement ou un vrai outil comptable, sans effectuer d'appel réel —
exactement le même principe que
`tmis.collaboration.notifications.channels.EmailChannel` (Sprint 8).
Brancher Stripe, GoCardless ou Sage/QuickBooks/Pennylane se fait en
implémentant ces deux ports, sans toucher `BillingEngine`.

## Où l'API l'expose

- `POST /api/v1/cabinet-os/billing/invoices` — crée une facture.
- `POST .../invoices/{id}/lines` — ajoute une ligne.
- `POST .../invoices/{id}/issue` — émet la facture.
- `POST .../invoices/{id}/payments` — enregistre un paiement.
- `GET .../invoices/{id}/total-due` — consulte le reste à payer.
