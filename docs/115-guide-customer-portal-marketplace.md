# Guide — Portail client et abonnements Marketplace (Sprint 20)

## Le portail client

`customer_portal.CustomerPortalEngine` est un agrégateur en lecture
seule — il ne mute jamais rien, il compose huit domaines déjà
possédés par d'autres moteurs (`identity_platform.users`/`roles`,
`subscriptions`, `plans`, `licenses`, `modules`, `usage`,
`tenant_settings`, `cabinet_os.billing`'s invoice store) en un seul
instantané :

```python
from tmis.business_platform.bootstrap import get_customer_portal_engine

portal = get_customer_portal_engine()
snapshot = portal.snapshot(firm_id)
# snapshot.users, .role_assignments, .subscription, .plan,
# .license_grants, .active_modules, .usage, .settings, .recent_invoices
```

Chaque champ de `CustomerPortalSnapshot` a exactement un moteur
propriétaire — le portail n'invente aucune logique métier, il ne fait
que la restituer.

## Abonnements Marketplace

`marketplace_subscriptions.MarketplaceSubscriptionEngine` étend
`platform_sdk.marketplace.MarketplaceEngine` (Sprint 13) — découverte/
installation/mise à jour/désinstallation d'extension — sans jamais
réimplémenter ce cycle de vie. Il ajoute ce qui manquait :
l'abonnement commercial (`ExtensionSubscription`), la licence API que
l'extension utilise pour rappeler TMIS (via `licenses.LicenseEngine`,
type `LicenseType.API`), et la facturation (via `cabinet_os.billing.
BillingEngine`, le même moteur que `billing.SubscriptionBillingEngine`
utilise pour l'abonnement SaaS de base).

```python
from tmis.business_platform.bootstrap import get_marketplace_subscription_engine

marketplace_subs = get_marketplace_subscription_engine()
subscription = marketplace_subs.subscribe(firm_id, plugin_id, monthly_price_usd=29.0)
marketplace_subs.unsubscribe(firm_id, plugin_id)  # révoque la licence, désinstalle l'extension
```

## Voir aussi

docs/111-architecture-business-platform.md,
docs/65-architecture-platform-sdk.md (Sprint 13 — Marketplace),
docs/103-architecture-identity-platform.md (Sprint 19 — users/roles).
