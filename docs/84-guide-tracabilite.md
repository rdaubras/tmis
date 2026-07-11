# Guide — Traçabilité

`tmis.ai_governance.traceability.TraceabilityEngine` construit la
chaîne complète exigée par le sprint : utilisateur, dossier, version
des modèles, prompts, réponses intermédiaires, validations humaines,
décisions finales — chaque élément relié à un identifiant unique.

## Enregistrer chaque élément

```python
from tmis.ai_governance.bootstrap import get_traceability_engine

trace = get_traceability_engine()
trace.record_user("firm-123", "prod-1", "user-1")
trace.record_case("firm-123", "prod-1", "dossier-bail-2026-01")
trace.record_model_version("firm-123", "prod-1", "claude-legal", "4.5")
trace.record_prompt("firm-123", "prod-1", "prompt-analyse-bail-v3")
trace.record_intermediate_response("firm-123", "prod-1", "resp-1", "Synthèse produite.")
trace.record_human_validation("firm-123", "prod-1", "val-1", "Approuvé par l'associé.")
trace.record_final_decision("firm-123", "prod-1", "dec-1", "Résiliation engagée.")
```

Chaque méthode `record_*` est une convenance autour de `record()` —
`record_model_version` construit par exemple une référence unique
`"{modèle}@{version}"` (ex. `claude-legal@4.5`).

## Consulter la chaîne complète

```python
for entry in trace.trace("firm-123", "prod-1"):
    print(entry.kind, entry.reference, entry.detail)
```

## Traçabilité vs. provenance vs. lineage

Trois concepts proches, volontairement séparés :

| Module | Répond à... |
|---|---|
| `traceability` | Quel a été le déroulement opérationnel de cette production ? |
| `provenance` | D'où vient chaque affirmation du texte, phrase par phrase ? |
| `lineage` | De quelle production antérieure celle-ci est-elle issue ? |

Voir docs/80-architecture-ai-governance.md pour le détail de cette
séparation.
