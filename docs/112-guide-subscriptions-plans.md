# Guide — Abonnements et plans (Sprint 20)

## Les cinq plans

`business_platform.plans.schemas.PlanName` : `TRIAL`, `BASIC`,
`PROFESSIONAL`, `BUSINESS`, `ENTERPRISE`. Chaque plan porte des
limites (`PlanLimits` : utilisateurs, stockage, appels IA/mois,
dossiers, workflows, agents, modèles IA autorisés, connecteurs
disponibles), un ensemble de `features` (chaînes gatant les modules —
voir docs/114-guide-feature-flags-modules.md) et un tarif mensuel/
annuel.

## Versionnement

`PlanCatalog.publish(name, limits, ...)` crée toujours une nouvelle
version immuable (`Plan.version` incrémenté) plutôt que de modifier un
plan existant. `Subscription.plan_id` référence la version exacte
vendue à un cabinet — republier le plan `professional` en version 2
ne change donc jamais silencieusement ce qu'un abonné a accepté en
version 1. `PlanCatalog.latest(name)` récupère toujours la dernière
version publiée pour un nouvel abonnement.

```python
from tmis.business_platform.bootstrap import get_plan_catalog
from tmis.business_platform.plans.schemas import PlanName

catalog = get_plan_catalog()
plan = catalog.latest(PlanName.PROFESSIONAL)
```

## Cycle de vie d'un abonnement

`SubscriptionStatus` : `TRIAL` → `ACTIVE` → (`PAST_DUE` ↔ `ACTIVE`) →
`CANCELLED`/`EXPIRED`.

```python
from tmis.business_platform.bootstrap import get_subscription_engine
from tmis.business_platform.subscriptions.schemas import BillingCycle

subscriptions = get_subscription_engine()
subscriptions.start_trial(firm_id, plan.id)
subscriptions.activate(firm_id, BillingCycle.MONTHLY)
```

`trial.TrialEngine` encapsule le parcours d'essai : `start`,
`extend(firm_id, extra_days)`, `convert_to_paid`,
`expire_if_needed`.

## Facturation et paiement

`billing.SubscriptionBillingEngine.invoice_for_subscription(firm_id)`
émet une facture d'une ligne (le montant du plan pour le cycle en
cours, calculé par `pricing.PricingEngine`) via
`cabinet_os.billing.BillingEngine` — le même moteur que celui utilisé
pour facturer les clients d'un cabinet. `invoicing.InvoicingEngine.
run_billing_cycle(firm_id)` ne facture que si `is_due` (statut actif
et période échue), puis avance explicitement la période via
`SubscriptionEngine.advance_period` — jamais par mutation directe de
l'objet retourné par le store. `payments.PaymentEngine.record_payment`
encaisse un règlement, `total_due` renvoie le solde restant.

## Voir aussi

docs/111-architecture-business-platform.md,
docs/42-guide-facturation.md (Sprint 9).
