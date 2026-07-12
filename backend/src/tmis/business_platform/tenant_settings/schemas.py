from dataclasses import dataclass
from enum import StrEnum


class InvoicingLanguage(StrEnum):
    FR = "fr"
    EN = "en"


@dataclass(slots=True)
class TenantSettings:
    """Per-firm *business* settings — currency, invoicing contact,
    billing-cycle preference. Distinct in scope from
    `identity_platform.configuration.IdentityConfiguration` (Sprint
    19), which governs authentication/session behaviour; a firm's
    invoicing language has nothing to do with its MFA policy, so
    the two are kept as separate aggregates rather than one bag of
    unrelated per-firm flags."""

    firm_id: str
    currency: str = "EUR"
    invoicing_language: InvoicingLanguage = InvoicingLanguage.FR
    invoicing_contact_email: str | None = None
    auto_renew: bool = True
