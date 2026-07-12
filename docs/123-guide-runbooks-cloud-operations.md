# Guide — Runbooks (Sprint 21)

## Bibliothèque par défaut

`runbooks.RunbooksEngine` est initialisé avec `library.DEFAULT_RUNBOOKS`
— les cinq procédures que le sprint cite explicitement en exemple :

| Slug | Titre | Déclencheur |
|---|---|---|
| `ai-provider-unavailable` | Fournisseur IA indisponible | Health check `ai_fabric` reporte DOWN |
| `slow-database` | Base de données lente | `cloud_operations.performance` détecte une latence DATABASE élevée |
| `platform-overload` | Surcharge plateforme | `cloud_operations.capacity` projette un dépassement de SLO imminent |
| `sync-failure` | Échec de synchronisation connecteur | Health check connecteur reporte des échecs répétés |
| `marketplace-incident` | Incident Marketplace | Une extension publiée cause des erreurs |

Chaque runbook porte une liste ordonnée d'étapes concrètes,
référençant les moteurs TMIS existants à consulter (jamais une
procédure abstraite déconnectée du code).

```python
from tmis.cloud_operations.bootstrap import get_runbooks_engine

runbooks = get_runbooks_engine()
runbook = runbooks.get("ai-provider-unavailable")
for step in runbook.steps:
    print(step.order, step.instruction)
```

## Étendre la bibliothèque

`RunbooksEngine.register(runbook)` ajoute (ou remplace, par `slug`)
une procédure spécifique à un déploiement — utile pour des runbooks
propres à un cabinet ou une infrastructure particulière, sans toucher
`library.DEFAULT_RUNBOOKS`.

## API REST

- `GET /cloud-operations/runbooks` — liste tous les runbooks
- `GET /cloud-operations/runbooks/{slug}` — détail d'un runbook (404
  si le slug n'existe pas)
