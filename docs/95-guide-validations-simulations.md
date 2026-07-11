# Guide — Validations & Simulations

## Validation humaine des actions critiques

`approval_gateway.ApprovalGatewayEngine` gate les actions critiques
(génération d'un document, envoi d'un courrier, enrichissement des
connaissances, lancement d'un workflow critique) derrière une
politique configurable par type d'action et par cabinet — sans
réimplémenter le workflow d'approbation, en réutilisant directement
`ai_governance.human_validation.HumanValidationEngine`.

```python
from tmis.workflow_automation.bootstrap import get_approval_gateway_engine
from tmis.workflow_automation.action_engine.schemas import ACTION_GENERATE_DRAFT
from tmis.ai_governance.human_validation.schemas import ValidationDecisionType

gateway = get_approval_gateway_engine()
gateway.configure("firm-123", ACTION_GENERATE_DRAFT, required=True)

if gateway.requires_approval("firm-123", ACTION_GENERATE_DRAFT):
    request = gateway.request_approval("firm-123", "action-1", "avocat-1", ("associe-1",))
    gateway.decide("firm-123", request.id, "associe-1", ValidationDecisionType.APPROVE)

print(gateway.is_approved("firm-123", "action-1"))
```

## Simuler un workflow sur des données fictives

`simulation.SimulationEngine` exécute uniquement les conditions
(niveau workflow et niveau étape) contre un contexte fictif —
**jamais** `action_engine` — garantissant qu'aucune donnée réelle
n'est jamais touchée pendant une simulation.

```python
from tmis.workflow_automation.bootstrap import get_simulation_engine

report = get_simulation_engine().simulate(workflow, context={"go": "yes"})
print(report.would_complete)
for step in report.steps:
    print(step.name, step.would_run, step.skip_reason)
```

Si une condition de niveau workflow échoue, `would_complete` est
`False` et `workflow_condition_failure` explique pourquoi — aucune
étape n'est même évaluée.

## Rollback des actions réversibles

`rollback.RollbackEngine` compense une action déjà exécutée, si un
`RollbackHandlerPort` est enregistré pour son type — sinon, il journal
explicitement l'absence de handler plutôt que d'échouer silencieusement.

```python
from tmis.workflow_automation.bootstrap import get_rollback_engine
from tmis.workflow_automation.rollback.schemas import RollbackResult

class CancelTaskHandler:
    action_type = "create_task"
    def compensate(self, action, context):
        return RollbackResult(compensated=True, detail="Tâche annulée")

get_rollback_engine().register(CancelTaskHandler())
```

Chaque tentative de rollback est journalisée, réussie ou non — même
convention "toujours journalisé" que `action_engine`.
