from enum import StrEnum


class BusinessNotificationType(StrEnum):
    """The business events the sprint's OBSERVABILITÉ section asks to
    be traceable and, where relevant, notified to a firm admin."""

    QUOTA_WARNING = "quota_warning"
    QUOTA_EXCEEDED = "quota_exceeded"
    PLAN_CHANGED = "plan_changed"
    TRIAL_ENDING = "trial_ending"
    INVOICE_ISSUED = "invoice_issued"
    PAYMENT_FAILED = "payment_failed"
    LICENSE_EXPIRING = "license_expiring"
