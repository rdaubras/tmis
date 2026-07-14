# Guide — Entity Resolution (Sprint 25)

## Le problème

Les trois graphes existants de TMIS ne partagent aucun identifiant :
"Jean Dupont" peut être `actor-1` dans `case_intelligence.relationships`,
`entity-42` dans `document_intelligence.knowledge` d'un autre dossier,
et l'auteur d'une note dans `cabinet_knowledge.ontology`. Aucun des
trois graphes ne peut, seul, répondre à "est-ce la même personne ?" —
ce n'est pas leur rôle et ce n'est le rôle d'aucun autre module
existant. `tmis.knowledge_graph.entity_resolution` comble ce manque.

## Le modèle

- `EntityOccurrence` : une référence (`origin`, `node_id`, `label`)
  vers ce qui pourrait être une même entité, dans l'un des trois
  graphes. `origin` réutilise `federation.GraphOrigin` — le seul
  vocabulaire "quel graphe" du bounded context.
- `ResolvedEntity` : l'entité canonique, avec toutes ses occurrences,
  un score de confiance, et un statut (`CONFIRMED`,
  `PENDING_VALIDATION`, `REJECTED`).

## Le score de confiance

`EntityResolutionEngine` normalise chaque label (`casefold`, espaces
compressés) puis calcule, pour chaque paire d'occurrences, un ratio de
similarité (`difflib.SequenceMatcher.ratio()`). Le score final est le
**minimum** de ces ratios — délibérément conservateur : une seule paire
mal appariée suffit à faire chuter la confiance de tout le groupe,
plutôt qu'une moyenne qui masquerait un mauvais appariement derrière de
bons.

```python
from tmis.knowledge_graph.entity_resolution.engine import EntityResolutionEngine
from tmis.knowledge_graph.entity_resolution.schemas import EntityOccurrence
from tmis.knowledge_graph.entity_resolution.store import InMemoryResolvedEntityStore
from tmis.knowledge_graph.federation.schemas import GraphOrigin
from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.store import InMemoryValidationStore

engine = EntityResolutionEngine(
    InMemoryResolvedEntityStore(),
    HumanValidationEngine(InMemoryValidationStore()),
    confidence_threshold=0.85,
)

resolved = engine.resolve(
    "firm-1",
    "user-1",
    [
        EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="actor-1", label="Jean Dupont"),
        EntityOccurrence(
            origin=GraphOrigin.DOCUMENT_KNOWLEDGE_GRAPH, node_id="entity-42", label="Jean Dupont"
        ),
    ],
)
```

## Sous le seuil : validation humaine, jamais un second mécanisme

Si le score est sous `confidence_threshold`, `resolve()` n'auto-confirme
jamais l'entité. Il appelle `HumanValidationEngine.request_simple`
(mode `SIMPLE` : un seul approbateur suffit) — le même moteur que tout
le reste de TMIS utilise pour la validation humaine
(`docs/38-guide-validations.md`, `docs/81-guide-politiques-gouvernance.md`).
`entity_resolution` ne construit jamais son propre système d'approbation.

```python
resolved = engine.resolve(
    "firm-1", "user-1", occurrences, approver_ids=("partner-1",)
)
# resolved.status is ResolutionStatus.PENDING_VALIDATION

engine.decide("firm-1", resolved.id, "partner-1", ValidationDecisionType.APPROVE)
# -> ResolutionStatus.CONFIRMED
```

`decide()` relit le statut final de la `ValidationRequest` sous-jacente
et le traduit en `ResolutionStatus` (`APPROVED` → `CONFIRMED`,
`REJECTED` → `REJECTED`, sinon `PENDING_VALIDATION`) — il ne réimplémente
aucune logique d'approbation, il ne fait que refléter la décision de
`HumanValidationEngine`.

## Utiliser une résolution avec la fédération

Une fois résolue, une entité pilote une requête `federation` cross-scope :

```python
occurrences = [(o.origin, o.node_id) for o in resolved.occurrences]
neighborhoods = federation_engine.cross_scope_neighborhood("firm-1", occurrences)
```

Voir docs/145-architecture-knowledge-graph.md pour le rôle de
`FederationQueryEngine`, et docs/147-guide-semantic-intelligence.md
pour la différence avec un lien de similarité sémantique.

## Ce que ce module ne fait pas

- Il ne stocke aucun node ni edge des trois graphes existants —
  uniquement le résultat de la résolution (`ResolvedEntity`).
- Il ne décide jamais seul qu'une résolution à faible confiance est
  correcte — c'est toujours `HumanValidationEngine` qui tranche.
- Il ne calcule pas de similarité sémantique par embeddings — c'est le
  rôle de `semantic_intelligence`, sur un axe différent (labels
  courts, identité d'entité) de celui de la similarité de contenu.
