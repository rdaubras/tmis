# Guide — Gestion des incidents (Sprint 21)

## Cycle de vie

`incident_management.IncidentManagementEngine` implémente les quatre
étapes demandées par le sprint : **ouverture** → **suivi** →
**résolution** → **post-mortem**, plus un état terminal `CLOSED`.

```python
from tmis.cloud_operations.bootstrap import get_incident_management_engine
from tmis.cloud_operations.incident_management.schemas import IncidentSeverity

incidents = get_incident_management_engine()

incident = incidents.open_incident(
    "Fournisseur IA indisponible", "GPT-4 échoue depuis 5 minutes",
    IncidentSeverity.HIGH, firm_id="firm-123",
)
incidents.track(incident.id, "Panne confirmée sur le statut du fournisseur", author="ops-bot")
resolved = incidents.resolve(incident.id)
report = incidents.record_post_mortem(
    incident.id,
    root_cause="Panne fournisseur",
    impact="5 minutes de latence élevée",
    resolution="Bascule vers le modèle de secours",
    action_items=["Ajouter un second fournisseur"],
)
incidents.close(incident.id)
```

`track()` fait automatiquement transitionner un incident `OPEN` vers
`INVESTIGATING` — le premier suivi documente toujours qu'une enquête a
commencé.

## Modèle de rapport de post-mortem

`record_post_mortem` produit un `PostMortemReport` à structure fixe
(résumé, cause racine, impact, résolution, actions correctives, durée
en minutes calculée depuis `opened_at`/`resolved_at`) — le « modèle de
rapport » que le sprint demande, jamais un texte libre non structuré.

## API REST

- `POST /cloud-operations/incidents` — ouvre un incident
- `GET /cloud-operations/incidents` — liste les incidents ouverts
  (filtrable par `firm_id`)
- `POST /cloud-operations/incidents/{id}/resolve` — résout un incident
