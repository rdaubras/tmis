# Guide — Politiques de gouvernance IA

`tmis.ai_governance.policy_engine` gouverne les **productions** IA
(sorties déjà générées), pas les modèles — voir
`docs/73-architecture-ai-fabric.md` pour la gouvernance de modèle
(`tmis.ai_fabric.governance`), un sujet distinct.

## Créer une politique

```python
from tmis.ai_governance.bootstrap import get_policy_engine
from tmis.ai_governance.policy_engine.schemas import GovernancePolicyType

engine = get_policy_engine()

engine.create_policy(
    "firm-123",
    GovernancePolicyType.MANDATORY_VALIDATION_BEFORE_EXPORT,
    "Toute réponse doit être validée avant envoi au client.",
)

engine.create_policy(
    "firm-123",
    GovernancePolicyType.MIN_CONFIDENCE_THRESHOLD,
    "Seuil qualité minimal du cabinet.",
    min_confidence=0.7,
)

engine.create_policy(
    "firm-123",
    GovernancePolicyType.MANDATORY_REVIEW_FOR_CASE_TYPE,
    "Les dossiers pénaux nécessitent une relecture associé.",
    case_type="penal",
)
```

## Les cinq types de politique

| Type | Bloque quand... |
|---|---|
| `MANDATORY_VALIDATION_BEFORE_EXPORT` | `is_export=True` et `human_validated=False` |
| `MIN_CONFIDENCE_THRESHOLD` | `confidence_value` sous `min_confidence` |
| `FORBIDDEN_MODEL` | `forbidden_model_name` figure dans `model_names_used` |
| `MANDATORY_CITATIONS` | `citation_count == 0` |
| `MANDATORY_REVIEW_FOR_CASE_TYPE` | `case_type` correspond et `human_validated=False` |

## Évaluer une production

```python
from tmis.ai_governance.policy_engine.schemas import PolicyEvaluationContext

evaluation = engine.evaluate(
    PolicyEvaluationContext(
        firm_id="firm-123",
        production_id="prod-1",
        is_export=True,
        confidence_value=0.65,
        human_validated=False,
    )
)
print(evaluation.allowed)   # False
print(evaluation.reasons)   # une phrase par politique violée
```

`reasons` n'est jamais vide : en l'absence de toute politique
restrictive applicable, il contient la phrase "aucune politique
restrictive applicable" — la décision reste toujours explicable.

## Combiner avec les risques : le verdict de conformité

```python
from tmis.ai_governance.bootstrap import get_risk_engine, get_compliance_engine

risks = get_risk_engine().assess(
    citation_count=1, contradiction_count=0, source_age_days=100,
    confidence_value=0.65, human_validated=False,
)
verdict = get_compliance_engine().check("prod-1", evaluation, risks)
print(verdict.compliant, verdict.blocking_reasons, verdict.warnings)
```

Une production n'est jamais considérée comme définitive tant que
`verdict.compliant` n'est pas `True` — c'est la contrainte centrale du
sprint.

## Désactiver une politique

```python
engine.deactivate_policy(policy.id)
```

Une politique désactivée reste dans l'historique (`list_policies`
ne la retourne plus, mais elle n'est jamais supprimée).
