# Guide — Explicabilité

`tmis.ai_governance.explainability.ExplainabilityEngine` génère, pour
une production, un rapport pensé pour être lu par un avocat — jamais
un développeur.

## Générer une explication

```python
from tmis.ai_governance.bootstrap import get_explainability_engine
from tmis.ai_governance.explainability.schemas import IgnoredElement

engine = get_explainability_engine()
report = engine.generate(
    "firm-123",
    "prod-1",
    summary="Le bail peut être résilié sur la base de la clause résolutoire.",
    steps_followed=("Question", "Analyse", "Recherche", "Brouillon"),
    agents_involved=("Analyste documentaire", "Rédacteur"),
    models_used=("gpt-4-legal", "claude-legal"),
    legal_references=("Code civil, art. 1103",),
    documents_consulted=("Contrat de bail commercial",),
    ignored_elements=(
        IgnoredElement("Clause de garantie", "Non pertinente au litige en cours"),
    ),
)
```

## Les sept questions couvertes

| Champ | Répond à... |
|---|---|
| `summary` | Pourquoi cette réponse ? |
| `steps_followed` | Quelles étapes ont été suivies ? |
| `agents_involved` | Quels agents sont intervenus ? |
| `models_used` | Quels modèles IA ont participé ? |
| `legal_references` | Quelles références juridiques ? |
| `documents_consulted` | Quels documents ont été consultés ? |
| `ignored_elements` | Quels éléments ont été ignorés, et pourquoi ? |

`ignored_elements` est le champ le plus souvent oublié dans les
systèmes d'explicabilité : chaque élément écarté porte une
`justification` obligatoire, jamais un simple silence.

## Historique et dernière version

```python
engine.history("firm-123", "prod-1")   # tout l'historique, jamais réécrit
engine.latest("firm-123", "prod-1")    # le rapport le plus récent, ou None
```

## Produire un rapport formaté

```python
from tmis.ai_governance.bootstrap import get_report_generator
from tmis.ai_governance.reporting.schemas import ReportType

report_doc = get_report_generator().generate(
    ReportType.EXPLAINABILITY, "firm-123", "prod-1", report=report
)
```

Voir docs/85-reference-api-ai-governance.md pour l'équivalent REST
(`POST /ai-governance/explanations`, `GET
/ai-governance/explanations/{production_id}`).
