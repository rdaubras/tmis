# Guide : ajouter un nouveau moteur d'analyse au Case Intelligence Engine

Chaque capacité du CIE (fusion d'acteurs, extraction de faits,
détection d'incohérences, détection de questions juridiques,
résumé...) est un port avec une implémentation heuristique par défaut.
Ajouter un nouveau moteur, ou en remplacer un, suit toujours le même
principe : **une classe qui implémente le port, injectée dans
`CaseIntelligenceWorkflow`** — jamais une modification du workflow
lui-même.

## Étapes générales

1. Repérer le port concerné :
   - `actors.ports.ActorMergerPort` — résolution/fusion d'acteurs ;
   - `facts.ports.FactEnginePort` — agrégation de faits ;
   - `evidence.ports.EvidenceLinkerPort` — niveau de confiance des preuves ;
   - `timeline.ports.TimelineConsolidatorPort` — chronologie consolidée ;
   - `issues.ports.IssueDetectorPort` — détection de questions juridiques ;
   - `search.ports.CaseSearchPort` — recherche unifiée ;
   - `summaries.ports.SummaryGeneratorPort` — résumés de dossier.
2. Créer la classe dans le module correspondant, en implémentant
   uniquement les méthodes du port (voir l'exemple ci-dessous).
3. L'injecter dans `CaseIntelligenceWorkflow(...)` (ou dans
   `tmis.case_intelligence.bootstrap.get_case_intelligence_workflow` pour
   le déploiement par défaut).
4. Ajouter les tests unitaires du nouveau moteur, puis un test
   d'intégration si son comportement doit être vérifié dans le flux
   complet (voir `backend/tests/integration/case_intelligence/`).

## Exemple : un détecteur de questions juridiques plus riche

```python
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.issues.schemas import LegalIssue

class ContractRiskIssueDetector:
    """Implémente `IssueDetectorPort` : ajoute une détection de risque
    contractuel aux règles heuristiques existantes."""

    def __init__(self, base_detector: IssueDetectorPort) -> None:
        self._base_detector = base_detector

    def detect(self, profile: CaseProfile) -> list[LegalIssue]:
        issues = self._base_detector.detect(profile)
        # ... règles additionnelles, ou appel à TMISKernel.complete()
        # pour une évaluation plus fine (jamais un fournisseur directement)
        return issues
```

```python
workflow = CaseIntelligenceWorkflow(
    issue_detector=ContractRiskIssueDetector(HeuristicIssueDetector()),
)
```

Ce patron de **décoration** (envelopper l'implémentation par défaut
plutôt que la remplacer entièrement) fonctionne pour n'importe quel
port du CIE et permet de composer plusieurs règles sans dupliquer la
logique existante.

## Contrainte à respecter systématiquement

Aucun moteur d'analyse n'appelle un fournisseur de modèle ou un
connecteur directement. S'il a besoin d'une capacité IA, il reçoit un
`TMISKernel` (ou un port restreint comme `SummaryKernelPort`, voir
`tmis.case_intelligence.summaries.ports`) en dépendance injectée — jamais
un import direct de `tmis.ai.providers` (voir docs/10-ai-kernel.md).

## Ajouter un nouveau type de nœud au graphe de relations

`relationships.schemas.CaseNodeType` liste les types de nœuds actuels
(`ACTOR`, `DOCUMENT`, `EVENT`, `FACT`, `EXHIBIT`, `ISSUE`). Pour en
ajouter un :

1. Étendre l'énumération `CaseNodeType`.
2. Ajouter la construction des nœuds/arêtes correspondants dans
   `knowledge.CaseKnowledgeAggregator.update()`.
3. `relationships.ports.CaseGraphPort` et son implémentation
   `InMemoryCaseGraph` n'ont besoin d'aucune modification : ils sont
   génériques sur `CaseNode`/`CaseEdge`.
