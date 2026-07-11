# Guide des Workflows (Sprint 13)

## Un workflow est de la donnée, jamais du code

`tmis.platform_sdk.workflow_sdk.WorkflowDefinition` décrit un
enchaînement d'étapes entièrement déclaratif :

```python
WorkflowDefinition(
    id="workflow-validation",
    name="Validation de dépense",
    steps=(
        WorkflowStep(
            id="check-amount", name="Vérifier le montant", action="check_amount",
            condition=WorkflowCondition("amount", ConditionOperator.LESS_THAN, 1000),
            on_success="auto-approve", on_failure="request-partner-approval",
        ),
        WorkflowStep(id="auto-approve", name="Approbation automatique", action="approve"),
        WorkflowStep(id="request-partner-approval", name="Aval associé", action="flag"),
    ),
    trigger_events=("TaskCompleted",),
    validations=("amount doit être un nombre positif",),
)
```

Aucun champ ne contient de code à exécuter — `condition` est un
triplet `(champ, opérateur, valeur)` interprété par un nombre fixe
d'opérateurs (`eq`, `neq`, `exists`, `not_exists`, `gt`, `lt`), et
`action` est un **nom** résolu dans un registre fermé
(`WorkflowActionRegistry`), jamais une chaîne évaluée. C'est la
garantie de sécurité du sprint : aucune extension ne peut contourner
les règles de sécurité de TMIS en embarquant du code arbitraire dans
un workflow.

## Exécution

```python
registry = WorkflowActionRegistry()
registry.register("check_amount", check_amount_handler)
registry.register("approve", approve_handler)
registry.register("flag", flag_handler)

executor = WorkflowExecutor(registry)
result = await executor.run(workflow, context, {"amount": 500})
# result.executed_step_ids, result.final_context, result.success
```

L'exécution part de la première étape et suit `on_success`/
`on_failure` selon que la condition de l'étape est vraie et que
l'action associée réussit. Une étape sans condition est toujours
"réussie" ; une action inconnue ou qui lève une exception prend la
branche `on_failure`. Le nombre d'itérations est borné
(`len(steps) * 2`), pour qu'un cycle accidentel dans une définition
écrite à la main ne puisse jamais bloquer l'appelant.

## Export / import

```python
from tmis.platform_sdk.workflow_sdk.serialization import to_json, from_json

payload = to_json(workflow)     # str JSON portable
restored = from_json(payload)   # WorkflowDefinition identique
```

Un workflow peut donc être exporté d'un cabinet, partagé, puis
réimporté dans un autre — ou publié comme plugin dans la Marketplace.

## Empaqueter un workflow comme plugin

```python
class MyWorkflowPlugin(BaseWorkflowPlugin):
    def __init__(self) -> None:
        super().__init__(plugin_id="my-workflow", definition=MY_DEFINITION, actions=MY_REGISTRY)
```

`BaseWorkflowPlugin.invoke()` exécute la définition et publie un
évènement `TaskCompleted` — voir l'exemple complet dans
`tmis.platform_sdk.examples.workflow_validation`.
