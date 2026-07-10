# Guide — Notifications

## Canaux disponibles

`tmis.collaboration.notifications.schemas.NotificationChannel` :
`IN_APP`, `EMAIL`, `WEBHOOK`. Chacun est implémenté derrière
`NotificationChannelPort` (`send(notification) -> None`) :

- `InAppChannel` : ne fait rien — la notification est déjà persistée
  par `NotificationEngine`, elle est donc visible en application dès
  sa création.
- `EmailChannel` / `WebhookChannel` : **interfaces** au sens du brief
  du Sprint 8 — elles enregistrent dans `self.sent` ce qui serait
  envoyé/posté, sans effectuer d'E/S réelle. Le branchement SMTP ou
  HTTP réel se fait derrière ce même port, plus tard.

## Envoyer une notification

```python
from tmis.collaboration.notifications.engine import NotificationEngine
from tmis.collaboration.notifications.schemas import NotificationChannel

engine = NotificationEngine()
notifications = engine.dispatch(
    workspace_id, recipient_id, "task_assigned", {"task_id": task_id},
    [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
)
```

Un dispatch vers *n* canaux crée *n* `Notification` distinctes — chaque
canal garde son propre statut de lecture (`read_at`), car
« notifié en application » et « notifié par e-mail » sont deux faits
différents.

## Consulter et marquer comme lue

```python
engine.list_for_recipient(member_id)
engine.mark_read(notification_id)
```

Via l'API : `GET /api/v1/collaboration/notifications/{recipient_id}`
et `POST /api/v1/collaboration/notifications/{id}/read`.

## Notifications déclenchées par une mention

`mentions.MentionEngine` appelle `NotificationEnginePort.dispatch(...)`
pour chaque `@user:<id>` résolu dans un commentaire — voir
docs/33-legal-collaboration.md (« Comment Engine et Mentions ») pour
la limite actuelle sur `@team:`/`@firm:`.

## Ajouter un canal (ex. Slack, SMS)

1. Implémenter `NotificationChannelPort.send()`.
2. L'enregistrer dans le dict passé au constructeur de
   `NotificationEngine`, ou l'ajouter à `_DEFAULT_CHANNELS`
   (`notifications/engine.py`) si le canal doit être disponible
   partout par défaut.
3. Aucun appelant de `dispatch()` n'a besoin de changer — c'est
   exactement le rôle du port.
