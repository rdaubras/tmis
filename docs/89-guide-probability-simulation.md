# Guide — Probability & Simulation : conformité "aucune prédiction judiciaire"

Ce guide documente comment `probability/` et `simulation/` satisfont
les deux contraintes les plus strictes du sprint : "aucune prédiction
de résultat d'un procès ne doit être présentée comme certaine" et
"aucune prédiction judiciaire ne doit être fournie dans ce sprint"
(pour la simulation).

## `probability/` : vraisemblance qualitative, jamais un pronostic

`ProbabilityAssessment` ne porte **aucun** champ numérique de
probabilité de gain de procès. `Likelihood` est une énumération à
trois valeurs (`LOW`/`MEDIUM`/`HIGH`), et elle s'applique toujours à un
**sous-élément** d'une stratégie — jamais au dossier dans son
ensemble.

```python
from tmis.strategic_intelligence.bootstrap import get_probability_engine

assessment = get_probability_engine().assess(
    "Recevabilité du témoignage du collègue",
    supporting_count=3,
    contradicting_count=1,
)
print(assessment.likelihood, assessment.rationale)
```

`supporting_count`/`contradicting_count` sont fournis par l'appelant
(typiquement à partir de `case_intelligence.evidence` ou
`evidence_gap`) — l'engine ne connaît jamais le dossier entier, ce qui
rend structurellement impossible toute évaluation d'issue globale.

## `simulation/` : structurel, jamais prédictif

`SimulationEngine.run()` ne fait que repérer, par correspondance de
mots-clés insensible à la casse, quelles stratégies mentionnent les
éléments d'un changement hypothétique. Il opère uniquement sur des
copies de texte que l'appelant lui fournit — jamais sur des données
réelles mutables — et son résultat (`SimulationResult`) ne contient
que `affected_strategy_ids` et des `notes` explicatives.

```python
from tmis.strategic_intelligence.bootstrap import get_simulation_engine

result = get_simulation_engine().run(
    "dossier-1",
    strategy_texts={
        "strategy-negociation": "Fondée sur le témoignage du collègue et les emails",
        "strategy-procedurale": "Stratégie procédurale sans lien avec le témoignage",
    },
    hypothetical_changes=("témoignage",),
)
print(result.affected_strategy_ids)  # ('strategy-negociation',)
```

Aucun champ `win_probability`, `outcome` ou `prediction` n'existe dans
`SimulationResult` ni dans `ProbabilityAssessment` — vérifié
explicitement par
`test_simulation_engine_never_predicts_an_outcome` et
`test_probability_assessment_never_scopes_to_case_outcome`
(`tests/unit/strategic_intelligence/`).
