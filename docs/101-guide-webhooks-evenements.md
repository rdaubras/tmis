# Guide — Webhooks et Événements (Sprint 18)

## `event_bridge` : la hiérarchie d'événements du LIH

`tmis.integration_hub.event_bridge` a sa propre hiérarchie
`IntegrationEvent`/`IntegrationEventBus`, indépendante des autres bus
de TMIS (`collaboration.event_bus`, `ai_governance.events`,
`workflow_automation.event_bus`) — même patron établi depuis le
Sprint 8.

Quatre types d'événements :

- `ExternalRecordChanged` — une notification de changement entrante
  (webhook reçu ou diff détecté par un polling) ;
- `SyncCompleted` — une synchronisation vient de se terminer ;
- `ConnectorAuthFailed` — un échec d'authentification côté
  connecteur ;
- `OutboundNotificationRequested` — un changement côté TMIS à pousser
  vers le système externe.

## `EventBridge` : le pont explicite

`EventBridge` est le seul point du LIH qui importe
`workflow_automation` directement — c'est précisément son rôle : il
s'abonne à `ExternalRecordChanged` sur l'`IntegrationEventBus` et
republie un `IntegrationEventReceived` (déjà défini côté
`workflow_automation.event_bus` depuis le Sprint 17) sur le
`WorkflowEventBus`, pour que `trigger_engine` puisse déclencher un
workflow sur un événement venu d'un système externe.

```python
bridge = EventBridge(integration_bus, workflow_bus)  # s'abonne dès la construction
await integration_bus.publish(ExternalRecordChanged(
    firm_id="f1", connector_id="crm-demo", direction=EventDirection.INBOUND,
    entity_type="client", external_id="cli-42", payload={"name": "Société X"},
))
# -> workflow_bus reçoit IntegrationEventReceived(integration_name="crm-demo", label="client", ...)
```

## Webhooks entrants : toujours signés

`WebhookEngine.receive_inbound(subscription, raw_body, signature,
entity_type, external_id, payload)` vérifie la signature HMAC-SHA256
(`webhooks.signing.verify_signature`) avant toute chose. Signature
invalide → `False`, aucun événement publié. Signature valide → publie
`ExternalRecordChanged` sur l'`IntegrationEventBus` (donc, via
`EventBridge`, jusqu'au `WorkflowEventBus`).

```python
signature = sign_payload(subscription.secret, raw_body)  # côté émetteur
ok = await webhook_engine.receive_inbound(subscription, raw_body, signature, "client", "cli-42", payload)
```

## Webhooks sortants : dispatch filtré par type d'événement

```python
results = await webhook_engine.dispatch_outbound(
    firm_id, connector_id, "client.updated", {"name": "Société X"}
)
```

Chaque abonnement `OUTBOUND` dont `event_types` est vide ou contient
`"client.updated"` reçoit l'appel, signé avec son propre secret. Le
transport HTTP réel est une entrée découplée
(`WebhookSenderPort.send`) — `LoggingWebhookSender` (livré) journalise
au lieu d'émettre un vrai appel HTTP ; un déploiement branche un
sender basé sur `httpx` sans toucher `WebhookEngine`.

## API REST

Voir `docs/102-reference-api-integration-hub.md` pour
`POST /integration-hub/webhooks` (créer un abonnement) et
`POST /integration-hub/webhooks/{id}/inbound` (livraison entrante).
