import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ExtensionSubscriptionStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


def new_extension_subscription_id() -> str:
    return f"extsub-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class ExtensionSubscription:
    """A firm's commercial subscription to one Marketplace plugin —
    distinct from the firm's base SaaS `subscriptions.Subscription`.
    Ties together the plugin's lifecycle (`platform_sdk.extensions.
    ExtensionInstance`, via `MarketplaceEngine`) and the license grant
    (`licenses.LicenseGrant`, always `LicenseType.API`) that lets the
    plugin call back into TMIS on the firm's behalf."""

    id: str
    firm_id: str
    plugin_id: str
    license_grant_id: str
    monthly_price_usd: float
    status: ExtensionSubscriptionStatus = ExtensionSubscriptionStatus.ACTIVE
    subscribed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
