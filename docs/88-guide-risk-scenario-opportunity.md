# Guide — Risk Matrix, Scenario Builder, Opportunity Engine & Evidence Gap

## Matrice de risques configurable

`risk_matrix.RiskMatrixEngine` combine cinq facteurs déjà calculés en
un score unique, toujours accompagné d'une explication en français —
même patron que `ai_governance.confidence.GovernanceConfidenceEngine`,
réimplémenté localement plutôt qu'importé (bounded context distinct).

```python
from tmis.strategic_intelligence.bootstrap import get_risk_matrix_engine

result = get_risk_matrix_engine().evaluate(
    "strategy-negociation-1",
    documentary_solidity=0.7,
    reasoning_coherence=0.8,
    evidence_dependency=0.4,
    uncertainty=0.3,
    requires_human_validation=True,
)
print(result.score, result.explanation)
```

Les critères par défaut (`DEFAULT_CRITERIA`) sont pondérés mais
remplaçables au cas par cas via le paramètre `criteria=`, satisfaisant
l'exigence "critères configurables" du sprint.

## Scénarios what-if

`scenario_builder.ScenarioBuilderEngine` produit par défaut trois
variantes — favorable, défavorable, intermédiaire — extensibles via un
registre de `ScenarioVariantBuilderPort` (même patron que
`ai_governance.bias_detection.BiasDetectorPort`).

```python
from tmis.strategic_intelligence.bootstrap import get_scenario_builder_engine

scenarios = get_scenario_builder_engine().build_scenarios(
    "dossier-1", "Licenciement contesté", hypotheses=("Absence de motif",)
)
```

Chaque `Scenario` porte toujours des `limitations` : "ce scénario est
une exploration structurée, non une prédiction du résultat du procès."

## Opportunités et éléments manquants

`opportunity_engine.OpportunityEngine.find()` repère les arguments
inexploités, les documents complémentaires à obtenir, les clauses à
vérifier et signale un besoin de recherche additionnelle quand moins de
deux arguments principaux sont recensés — chaque `OpportunityFinding`
porte une `justification` non vide.

`evidence_gap.EvidenceGapEngine.identify()` transforme la liste
`missing_evidence` d'une stratégie en `EvidenceGap` structurés,
classés par impact estimé selon leur ordre d'apparition (le premier
élément listé est traité comme le plus prioritaire par l'appelant).

```python
from tmis.strategic_intelligence.bootstrap import get_opportunity_engine, get_evidence_gap_engine

findings = get_opportunity_engine().find(
    "strategy-1", missing_evidence=("Témoignage d'un collègue",)
)
gaps = get_evidence_gap_engine().identify(
    "strategy-1", ("Témoignage d'un collègue", "Relevé d'horaires")
)
```
