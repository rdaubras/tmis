# Référence API — Cloud Operations & Observability Platform (Sprint 21 + 22)

Base path : `/cloud-operations` — **délibérément hors** de
`/api/v1`, **non authentifié**, monté directement sur `app` dans
`main.py` à côté de `platform.api.routes`, sur le même principe déjà
établi là : « metrics/health endpoints sont une préoccupation
opérationnelle, pas une API métier versionnée ».

| Méthode | Chemin | Description |
|---|---|---|
| GET | `/metrics/{category}` | Historique + moyenne d'une catégorie de métrique (`?firm_id=`) |
| GET | `/traces/{trace_id}` | Arbre de spans d'une trace + durée totale |
| GET | `/alerts` | Historique des alertes déclenchées (`?firm_id=`) |
| POST | `/alerts/rules` | Configure une règle d'alerte |
| POST | `/alerts/evaluate` | Évalue toutes les règles actives (`?firm_id=`) |
| GET | `/dashboards/overview` | Vue plateforme + workflows + intégrations (+ IA/sécurité/business si `firm_id`) |
| GET | `/health` | Readiness des 12 composants (7 plateforme + 5 contextes métier) |
| GET | `/sla/{service_name}/{metric_type}` | Indicateur SLA calculé |
| GET | `/slo/{service_name}/{metric_type}` | Statut SLO + budget d'erreur restant |
| GET | `/capacity/{category}` | Projection de croissance (`?firm_id=&periods_ahead=`) |
| GET | `/performance` | Snapshot temps de réponse/débit (`?firm_id=`) |
| GET | `/profiling/{finding_type}` | Top offenders + recommandations (`?limit=`) |
| GET | `/cache/{cache_name}` | Statistiques hit/miss/taille/éviction |
| GET | `/queues/{queue_name}` | Statistiques taille/débit/attente/erreurs |
| GET | `/errors/recent` | Erreurs récentes cross-module (`?limit=`) |
| GET | `/incidents` | Incidents ouverts (`?firm_id=`) |
| POST | `/incidents` | Ouvre un incident |
| POST | `/incidents/{incident_id}/resolve` | Résout un incident |
| GET | `/runbooks` | Liste tous les runbooks |
| GET | `/runbooks/{slug}` | Détail d'un runbook (404 si inconnu) |
| GET | `/diagnostics` | Rapport composé santé/performance/erreurs/trace (`?firm_id=&trace_id=`) |
| POST | `/chaos/{scenario}` | Exécute un scénario de chaos testing (`?authorized=`) |

### Sprint 22 — 14 endpoints supplémentaires

| Méthode | Chemin | Description |
|---|---|---|
| GET | `/audit/{firm_id}` | Timeline d'audit fusionnée (sécurité + IA + workflow), triée par date |
| GET | `/cost/{firm_id}` | Snapshot de coût IA (par modèle, par utilisateur, franchissements de seuil) |
| GET | `/ai-quality/{firm_id}` | Snapshot télémétrie modèle (délégué à `ai_fabric.telemetry`) |
| POST | `/ai-quality/{firm_id}/scan` | Scanne un texte (`?text=`) pour hallucination/biais et historise les incidents détectés |
| GET | `/ai-quality/incidents/recent` | Derniers incidents qualité IA historisés (`?limit=`) |
| GET | `/workflow-monitoring` | Snapshot agrégé des exécutions de workflow (durée, erreurs, annulations) |
| GET | `/integration-monitoring` | Vue d'ensemble par connecteur (opérations, taux de réussite, durée) |
| GET | `/tenants/{firm_id}` | Snapshot tenant (MRR, coût IA, quotas, incidents ouverts) — 404 si le cabinet n'a pas d'abonnement |
| GET | `/security-monitoring` | Vue d'ensemble plateforme des événements de sécurité par type |
| GET | `/retention/{category}` | Politique de rétention pour une catégorie de données d'observabilité |
| POST | `/retention/{category}` | Définit la rétention (`?retention_days=`) pour une catégorie |
| GET | `/exports/incidents` | Exporte les incidents (`?export_format=csv\|json&firm_id=`) |
| GET | `/exports/metrics/{category}` | Exporte l'historique d'une catégorie de métrique (`?export_format=`) |

Voir docs/126-architecture-cloud-operations-sprint22.md pour le détail
architectural de ces 9 sous-modules et docs/127 à docs/131 pour les
guides associés.

Les fonctions de route retournent des `dict[str, object]` directement
(pas de couche `schemas.py` Pydantic dédiée), sur le même patron que
`platform.api.routes` — cohérent avec le statut « opérationnel, pas
métier versionné » de cette API. OpenAPI est généré automatiquement
par FastAPI (`/docs`, `/openapi.json`).

## Codes d'erreur

- `404` : ressource introuvable (trace/runbook/règle d'alerte
  inconnue, pas assez d'historique pour une projection de capacité).
- `403` : `POST /chaos/{scenario}` en environnement `production` sans
  `authorized=true` — verrou de sécurité imposé par le sprint,
  jamais contournable côté client.

## Voir aussi

docs/118-architecture-cloud-operations.md.
