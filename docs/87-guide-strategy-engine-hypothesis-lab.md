# Guide — Strategy Engine & Hypothesis Lab

## Générer plusieurs stratégies coexistantes

```python
from tmis.strategic_intelligence.bootstrap import get_strategy_engine

engine = get_strategy_engine()
strategies = engine.generate(
    case_id="dossier-licenciement-2026-03",
    question="Comment défendre ce salarié ?",
    hypotheses=("Licenciement sans cause réelle et sérieuse",),
    main_arguments=("Absence de motif valable",),
    counter_arguments=("Faute grave alléguée par l'employeur",),
    available_evidence=("Bulletins de salaire", "Échanges emails"),
    missing_evidence=("Témoignage d'un collègue",),
)
for s in strategies:
    print(s.strategy_type, s.confidence, s.limitations)
```

`generate()` retourne **une stratégie par type candidat**
(`DEFAULT_STRATEGY_TYPES` : Négociation amiable, Action prud'homale,
Stratégie transactionnelle, Stratégie procédurale) — aucune n'est
jamais exclue, même quand la confiance est faible. Chaque `Strategy`
porte toujours au moins une limitation : "cette stratégie est une
proposition ; elle ne constitue pas une décision juridique définitive."

## Le laboratoire d'hypothèses

`hypothesis_lab` gère un cycle de vie historisé —
`PROPOSED → SUPPORTED → MERGED/INVALIDATED/ARCHIVED` — repris du
patron `ALLOWED_TRANSITIONS` de `cabinet_knowledge.governance`.

```python
from tmis.strategic_intelligence.bootstrap import get_hypothesis_lab_engine

lab = get_hypothesis_lab_engine()
a = lab.create("firm-123", "dossier-1", "Licenciement sans cause réelle")
b = lab.create("firm-123", "dossier-1", "Licenciement pour faute grave contestable")

comparison = lab.compare("firm-123", a.id, b.id)
print(comparison.similarity, comparison.shared_terms)

merged = lab.merge("firm-123", a.id, b.id, actor="avocat-1")
# a et b passent automatiquement à MERGED ; merged.parent_ids == (a.id, b.id)

lab.invalidate("firm-123", merged.id, actor="avocat-1", reason="Non corroborée par les pièces")
```

Chaque transition ajoute un `HypothesisEvent` — jamais réécrit — au
journal consultable via `lab.history(firm_id, hypothesis_id)`.

## Différence avec `legal_reasoning.strategy` (Sprint 6)

`legal_reasoning.strategy.HeuristicStrategyEngine` produit une
`StrategyOption` **par hypothèse** — une option tactique locale liée à
une seule piste de raisonnement. `strategic_intelligence.strategy_engine`
produit une `Strategy` **par approche globale**, qui peut s'appuyer sur
plusieurs hypothèses. Les deux moteurs coexistent délibérément à des
échelons différents ; consulter les hypothèses du `legal_reasoning` (via
`case_intelligence`) reste un bon point de départ pour peupler le champ
`hypotheses` d'une `Strategy`.
