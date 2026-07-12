# Démonstration — Sprint 18 : intégrations, synchronisation et webhooks

Script : `backend/scripts/demo_integration_hub.py`
(`python -m scripts.demo_integration_hub` depuis `backend/`).
Cabinet fictif : "Cabinet Démo Lefèvre & Associés — Intégrations"
(`firm-demo-lih`), isolé des autres scripts de démonstration.

## 1. Connecteurs de référence installés

Les 7 connecteurs de démonstration (`messaging`, `calendar`,
`document_storage`, `esignature`, `dms`, `billing`, `crm`) sont
enregistrés au démarrage via `developer_sdk.register_connector`, tous
`active`. La santé globale (`platform.health.HealthCheckEngine`
composé par `integration_hub.health`) rapporte `up` — un composant par
connecteur :

```
messaging-demo       Messagerie (démo)                statut=active
calendar-demo        Agenda (démo)                    statut=active
document-storage-demo Stockage documentaire (démo)     statut=active
esignature-demo      Signature électronique (démo)    statut=active
dms-demo             GED (démo)                       statut=active
billing-demo         Facturation (démo)               statut=active
crm-demo             CRM (démo)                       statut=active
Santé globale : up (7 connecteur(s))
```

## 2. Synchronisation CRM avec mapping et conflit

Un `MappingProfile` transforme le champ source `name` en `NAME` majuscule
(transformation `uppercase`) avant comparaison avec un enregistrement
local fictif portant un nom différent. Le job utilise la stratégie
`HUMAN_VALIDATION` : le conflit est détecté, une demande de validation
est créée et l'écriture est **différée** (aucun enregistrement écrit
tant qu'aucune décision n'est prise) :

```
1re synchronisation : lus=1 écrits=0 conflits=1 en attente de validation=1
Conflit validé par un associé.
2e synchronisation (après validation) : conflits=1 en attente=0
```

`HumanValidationStrategy` réutilise
`ai_governance.human_validation.HumanValidationEngine` (Sprint 15)
sans aucune réimplémentation — la demande de validation est visible
via `human_validation_engine.history(firm_id, "crm-demo:cli-1")`
exactement comme n'importe quelle autre validation humaine de TMIS.

## 3. Webhook entrant signé -> événement de workflow

Un abonnement webhook entrant est créé pour `crm-demo`
(`secret-demo`). La livraison est signée HMAC-SHA256
(`webhooks.sign_payload`) puis vérifiée côté serveur
(`WebhookEngine.receive_inbound`) :

```
Livraison signée acceptée : True
Événement reçu côté workflow_automation : integration_name=crm-demo label=client payload={'name': 'Nouveau client détecté côté CRM'}
```

Le chemin complet est vérifié : signature valide → `WebhookEngine`
publie `ExternalRecordChanged` sur `event_bridge.IntegrationEventBus`
→ `EventBridge` (construit via `get_event_bridge()`) le traduit en
`IntegrationEventReceived` sur
`workflow_automation.event_bus.WorkflowEventBus` — le même événement
que `trigger_engine` (Sprint 17) écoute déjà pour déclencher un
workflow sur une intégration externe.

## Synthèse

Les trois scénarios démontrent les trois promesses centrales du
sprint : (1) un connecteur s'installe et se supervise sans code
spécifique à un fournisseur, (2) une synchronisation détecte un
conflit et le fait trancher par un humain plutôt que d'écraser
silencieusement une donnée, (3) un événement externe signé atteint le
moteur de workflows de TMIS par un chemin entièrement vérifié
(signature → bus d'intégration → pont → bus de workflow).
