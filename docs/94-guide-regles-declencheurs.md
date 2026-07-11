# Guide — Règles & Déclencheurs

## Déclencheurs extensibles

`trigger_engine` reconnaît sept types (`TriggerType`) : événement
métier, horaire, échéance, création de document, mise à jour d'un
dossier, validation, événement d'intégration. Chaque type a son
`TriggerMatcherPort` — un nouveau type se branche par `register()`,
jamais en modifiant `TriggerEngine`.

```python
from tmis.workflow_automation.bootstrap import get_trigger_engine
from tmis.workflow_automation.trigger_engine.schemas import Trigger, TriggerType, new_trigger_id
from tmis.workflow_automation.event_bus.schemas import DocumentCreated

engine = get_trigger_engine()
trigger = Trigger(
    id=new_trigger_id(), workflow_id="wf-1", trigger_type=TriggerType.DOCUMENT_CREATED,
    config={"document_type": "contrat"},
)
event = DocumentCreated(firm_id="firm-123", case_id="dossier-1", document_id="d1", document_type="contrat")
assert engine.matches(trigger, event)
```

`SCHEDULE` est le seul type qui ne passe **pas** par
`TriggerEngine.matches()` — il est déclenché par `scheduler.
SchedulerEngine.due()`, interrogé périodiquement plutôt qu'événementiel.

## Règles configurables sans modification du code

`rule_engine.RuleEngine` stocke des règles composées d'un arbre de
`Condition` — combinaison ET/OU/NON de comparateurs, dates et rôles —
créées et désactivées à l'exécution, sans redéploiement.

```python
from tmis.workflow_automation.bootstrap import get_rule_engine, get_condition_engine
from tmis.workflow_automation.condition_engine.schemas import Comparator, cond_and, cond_compare, cond_role_is

condition_engine = get_condition_engine()
rule_engine = get_rule_engine()

rule = rule_engine.create_rule(
    "firm-123", "Gros litige nécessitant validation associé",
    cond_and(cond_role_is("avocat"), cond_compare("amount", Comparator.GT, "50000")),
)
matches = rule_engine.evaluate_all("firm-123", {"role": "avocat", "amount": "80000"})
```

## Conditions réutilisables

Une expression fréquemment utilisée se déclare une fois et se
référence partout via `cond_ref()` :

```python
condition_engine.register_expression(
    "gros-litige", cond_compare("amount", Comparator.GT, "50000")
)
rule_engine.create_rule("firm-123", "Alerte gros litige", cond_ref("gros-litige"))
```

`ConditionEngine` accepte n'importe quelle donnée de contexte —
données du dossier, rôle utilisateur, type de procédure, état du
workflow, indicateurs de politique IA — assemblée par l'appelant
(convention d'entrées découplées, cohérente avec le reste de TMIS).
