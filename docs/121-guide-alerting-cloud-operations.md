# Guide — Alerting (Sprint 21)

## Configurer une règle

Une `AlertRule` est un seuil configurable sur une `MetricCategory` —
les cinq exemples du sprint (augmentation du temps de réponse, taux
d'erreur élevé, échec d'un workflow critique, indisponibilité d'un
fournisseur IA, dépassement de quota) sont tous exprimables comme un
seuil sur une catégorie de métrique, donc une seule forme de règle
couvre les cinq plutôt que cinq types d'alerte distincts.

```python
from tmis.cloud_operations.bootstrap import get_alerting_engine
from tmis.cloud_operations.alerting.schemas import AlertComparison, AlertSeverity
from tmis.cloud_operations.metrics.schemas import MetricCategory

alerting = get_alerting_engine()
rule = alerting.configure_rule(
    "high-latency",
    MetricCategory.RESPONSE_TIME,
    AlertComparison.GREATER_THAN,
    500.0,
    severity=AlertSeverity.CRITICAL,
    firm_id="firm-123",
    notify_recipient_id="ops-user-1",
)
```

Ou via l'API : `POST /cloud-operations/alerts/rules`.

## Évaluation et livraison

`evaluate(rule_id)` compare la dernière valeur historisée à la
règle ; en cas de dépassement, un `AlertEvent` est enregistré et — si
`firm_id` et `notify_recipient_id` sont renseignés — livré via
`collaboration.notifications.NotificationEngine` (Sprint 8), la seule
brique de livraison multi-canal de TMIS, plutôt qu'un second système
de notification. Les règles plateforme-globales (`firm_id=None`) sont
enregistrées et interrogeables mais jamais livrées — il n'y a pas de
cabinet à notifier.

`evaluate_all(firm_id=None)` évalue toutes les règles actives pour un
cabinet (ou toutes les règles plateforme si `firm_id=None`) — c'est
ce qu'appelle `POST /cloud-operations/alerts/evaluate`, à brancher sur
un ordonnanceur périodique en production.

## Historique

`GET /cloud-operations/alerts` retourne l'historique des alertes
déclenchées pour un cabinet (ou toutes si aucun `firm_id`), chacune
avec la sévérité, la valeur observée, le seuil et l'horodatage.
