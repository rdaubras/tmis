from tmis.business_platform.licenses.engine import LicenseEngine
from tmis.business_platform.licenses.schemas import LicenseType
from tmis.business_platform.marketplace_subscriptions.ports import ExtensionSubscriptionStorePort
from tmis.business_platform.marketplace_subscriptions.schemas import (
    ExtensionSubscription,
    ExtensionSubscriptionStatus,
    new_extension_subscription_id,
)
from tmis.cabinet_os.billing.engine import BillingEngine
from tmis.cabinet_os.billing.schemas import FeeType
from tmis.platform_sdk.extensions.schemas import ExtensionInstance
from tmis.platform_sdk.marketplace.engine import MarketplaceEngine
from tmis.platform_sdk.permissions.schemas import ExtensionPermission


class MarketplaceSubscriptionEngine:
    """The commercial layer over `platform_sdk.marketplace.
    MarketplaceEngine` (Sprint 13, discovery/install/update/
    uninstall) — never reimplements plugin lifecycle, only adds what
    it lacks: a paid subscription record, the API license grant a
    plugin needs to call back into TMIS (via `licenses.
    LicenseEngine`), and billing (via `cabinet_os.billing.
    BillingEngine`, the same engine `billing.SubscriptionBillingEngine`
    composes for the base SaaS subscription)."""

    def __init__(
        self,
        marketplace: MarketplaceEngine,
        licenses: LicenseEngine,
        billing: BillingEngine,
        store: ExtensionSubscriptionStorePort,
    ) -> None:
        self._marketplace = marketplace
        self._licenses = licenses
        self._billing = billing
        self._store = store

    def subscribe(
        self,
        firm_id: str,
        plugin_id: str,
        *,
        requested_permissions: frozenset[ExtensionPermission] = frozenset(),
        monthly_price_usd: float = 0.0,
    ) -> ExtensionSubscription:
        self._marketplace.install(firm_id, plugin_id, requested_permissions)
        grant = self._licenses.assign(firm_id, LicenseType.API, holder_id=plugin_id)
        if monthly_price_usd > 0:
            invoice = self._billing.create_invoice(firm_id, client_id=firm_id)
            self._billing.add_invoice_line(
                invoice.id,
                description=f"Extension {plugin_id} (abonnement mensuel)",
                quantity=1,
                unit_price=monthly_price_usd,
                fee_type=FeeType.FLAT_FEE,
            )
            self._billing.issue_invoice(invoice.id)
        subscription = ExtensionSubscription(
            id=new_extension_subscription_id(),
            firm_id=firm_id,
            plugin_id=plugin_id,
            license_grant_id=grant.id,
            monthly_price_usd=monthly_price_usd,
        )
        self._store.save(subscription)
        return subscription

    def unsubscribe(self, firm_id: str, plugin_id: str) -> ExtensionSubscription:
        subscription = self._require(firm_id, plugin_id)
        self._marketplace.uninstall(firm_id, plugin_id)
        self._licenses.revoke(firm_id, subscription.license_grant_id)
        subscription.status = ExtensionSubscriptionStatus.CANCELLED
        self._store.save(subscription)
        return subscription

    def update(self, firm_id: str, plugin_id: str) -> ExtensionInstance:
        return self._marketplace.update(firm_id, plugin_id)

    def list_for_firm(self, firm_id: str) -> list[ExtensionSubscription]:
        return self._store.list_for_firm(firm_id)

    def _require(self, firm_id: str, plugin_id: str) -> ExtensionSubscription:
        subscription = self._store.get(firm_id, plugin_id)
        if subscription is None:
            raise KeyError(f"no extension subscription for firm={firm_id} plugin={plugin_id}")
        return subscription
