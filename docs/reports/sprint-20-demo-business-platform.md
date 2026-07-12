# Démo — Sprint 20 (SaaS Business Platform)

Démonstration exécutée via `TestClient(app)` contre l'API réelle
(`/api/v1/business-platform`, `/api/v1/ai-fabric`) — sortie capturée
telle quelle.

## 1. Deux cabinets, deux plans différents

```
Cabinet Dupont (Basic): {'firm_id': 'cabinet-dupont', 'plan_id': 'plan-basic-v1', 'status': 'active', 'billing_cycle': 'monthly', ...}
Cabinet Martin (Business): {'firm_id': 'cabinet-martin', 'plan_id': 'plan-business-v1', 'status': 'active', 'billing_cycle': 'monthly', ...}
```

## 2. Le module `workflow_automation` n'est disponible que sur le plan Business

```
Cabinet Dupont workflow_automation: {'module': 'workflow_automation', 'active': False, 'available': False}
Cabinet Martin workflow_automation: {'module': 'workflow_automation', 'active': True, 'available': True}
```

Le plan Basic de Cabinet Dupont n'inclut pas la fonctionnalité
`workflow_automation` dans ses `features` — `ModuleRegistry.
is_available` le reflète automatiquement, sans configuration
manuelle.

## 3. Assignation de licences, isolées par cabinet

```
Cabinet Dupont licenses: 1
Cabinet Martin licenses: 2
```

## 4. Le quota `AI_CALLS` du plan Basic bloque au-delà de la limite

```
Premier appel (sous le quota): 200
Après épuisement du quota: 429 {'detail': "AI call quota exceeded for this firm's plan"}
```

`ai_fabric.api.routes.route_request` interroge désormais
`BusinessQuotaEngine.check_ai_calls` avant de router l'appel — voir
docs/116-guide-migration-business-platform.md.

## 5. Le tableau de bord commercial reflète la consommation

```
Cabinet Dupont dashboard: plan=basic mrr=49.0 ai_cost=0.0000
```

## 6. Le portail client agrège tout en une seule vue

```
Cabinet Martin portal: plan=business licenses=2 modules_actifs=15
```

`GET /customer-portal/{firm_id}` compose huit domaines
(`identity_platform.users`/`roles`, `subscriptions`, `plans`,
`licenses`, `modules`, `usage`, `tenant_settings`,
`cabinet_os.billing`) en une seule réponse — sans dupliquer aucune
logique métier déjà possédée par ces moteurs.
