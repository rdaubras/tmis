# Guide : ajouter un nouveau moteur de raisonnement au LRE²

Chaque capacité du Legal Reasoning Engine (hypothèses, arguments,
contre-arguments, preuves, conflits, confiance, stratégie,
explications, graphe de décision) est un port avec une implémentation
heuristique par défaut. Ajouter un nouveau moteur, ou en remplacer un,
suit toujours le même principe déjà établi par le Case Intelligence
Engine (voir docs/20-guide-nouveau-moteur-analyse.md) : **une classe qui
implémente le port, injectée dans `ReasoningOrchestrator`** — jamais une
modification de l'orchestrateur lui-même.

## Étapes générales

1. Repérer le port concerné :
   - `hypotheses.ports.HypothesisEnginePort` — génération d'hypothèses ;
   - `arguments.ports.ArgumentEnginePort` — construction d'arguments ;
   - `counter_arguments.ports.CounterArgumentEnginePort` — recherche de
     contre-arguments ;
   - `evidence.ports.EvidenceEnginePort` — liaison des preuves ;
   - `conflicts.ports.ConflictDetectorPort` — détection de conflits ;
   - `confidence.ports.ConfidenceEnginePort` — score de confiance ;
   - `strategy.ports.StrategyEnginePort` — pistes d'analyse ;
   - `explanations.ports.ExplanationEnginePort` — explication du
     raisonnement ;
   - `decision_graph.ports.DecisionGraphBuilderPort` — graphe de
     décision.
2. Créer la classe dans le module correspondant, en implémentant
   uniquement les méthodes du port.
3. L'injecter dans `ReasoningOrchestrator(...)` (ou dans
   `tmis.legal_reasoning.bootstrap.get_reasoning_orchestrator` pour le
   déploiement par défaut).
4. Ajouter les tests unitaires du nouveau moteur, puis un test
   d'intégration si son comportement doit être vérifié dans le
   raisonnement complet (voir
   `backend/tests/integration/legal_reasoning/`).

## Exemple : un générateur d'hypothèses appuyé sur le Kernel

```python
from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_research.search.schemas import ResearchResult


class KernelAugmentedHypothesisEngine:
    """Décore un moteur heuristique existant avec des hypothèses
    supplémentaires générées par `TMISKernel.complete()`."""

    def __init__(self, base_engine, kernel) -> None:
        self._base_engine = base_engine
        self._kernel = kernel  # un ReasoningKernelPort, jamais un provider

    def generate(
        self, question: str, facts: list[Fact], research_results: list[ResearchResult]
    ) -> list[Hypothesis]:
        hypotheses = self._base_engine.generate(question, facts, research_results)
        # ... appel à self._kernel.complete(...) pour une hypothèse plus
        # fine, ajoutée à la liste sans jamais retirer les précédentes.
        return hypotheses
```

```python
orchestrator = ReasoningOrchestrator(
    case_port=...,
    research_port=...,
    hypothesis_engine=KernelAugmentedHypothesisEngine(HeuristicHypothesisEngine(), kernel),
)
```

Ce patron de **décoration** (envelopper l'implémentation par défaut
plutôt que la remplacer entièrement) fonctionne pour n'importe quel
port du LRE² et permet de composer plusieurs règles sans dupliquer la
logique existante — exactement le même principe que
docs/20-guide-nouveau-moteur-analyse.md pour le CIE.

## Contraintes à respecter systématiquement

1. Aucun moteur n'appelle un fournisseur de modèle ou un connecteur
   directement. S'il a besoin d'une capacité IA, il reçoit un
   `ReasoningKernelPort` (jamais `tmis.ai.providers` ni
   `tmis.ai.connectors` importés directement).
2. Aucun moteur ne doit produire un document juridique final ni une
   conclusion juridique automatique — la synthèse reste un résumé
   transparent du raisonnement, toujours qualifiée comme telle.
3. Un `HypothesisEnginePort` ne doit jamais faire disparaître une
   hypothèse existante : ajouter, jamais remplacer.
4. Un `StrategyEnginePort` ne doit jamais choisir une seule option : il
   retourne toujours la liste complète des pistes envisageables.

## Ajouter un nouveau type de nœud au Decision Graph

`decision_graph.schemas.DecisionNodeType` liste les types actuels
(`QUESTION`, `HYPOTHESIS`, `ARGUMENT`, `COUNTER_ARGUMENT`, `EVIDENCE`,
`REFERENCE`, `SYNTHESIS`). Pour en ajouter un :

1. Étendre l'énumération `DecisionNodeType`.
2. Ajouter la construction des nœuds/arêtes correspondants dans
   `ChainDecisionGraphBuilder.build()`.
3. `decision_graph.ports.DecisionGraphBuilderPort` n'a besoin d'aucune
   modification : il reste générique sur `DecisionNode`/`DecisionEdge`.
