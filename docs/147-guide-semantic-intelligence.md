# Guide — Semantic Intelligence (Sprint 25)

## Similarité sémantique vs. "connecté à"

Les trois graphes existants modélisent des relations explicites : un
acteur *mentionné dans* un document, un document *contient* une
entité, une clause *related_to* une autre. Aucun n'exprime "ce
playbook et cette note se ressemblent, sans qu'un lien explicite
n'ait jamais été posé entre eux" — c'est une question de contenu, pas
de structure. `tmis.knowledge_graph.semantic_intelligence` répond à
cette question, en s'appuyant entièrement sur l'infrastructure
d'embeddings déjà existante (`tmis.ai.embeddings`, `tmis.ai.rag`) —
jamais un second fournisseur d'embeddings ou un second index vectoriel.

C'est le même principe que celui déjà documenté dans
`tmis.document_intelligence.knowledge.ports.KnowledgeGraphPort` : un
graphe de connaissance et un index vectoriel répondent à des questions
différentes ("quoi est connecté à quoi" vs. "quoi est sémantiquement
proche") et doivent pouvoir évoluer séparément.

## Le modèle

```python
from tmis.knowledge_graph.semantic_intelligence.engine import SemanticLinkEngine
from tmis.knowledge_graph.semantic_intelligence.store import InMemorySemanticLinkStore

engine = SemanticLinkEngine(InMemorySemanticLinkStore(), similarity_threshold=0.7)

links = await engine.link_objects([
    ("playbook-1", "Playbook de résiliation de bail commercial"),
    ("note-1", "Note sur la résiliation anticipée d'un bail commercial"),
    ("recette-1", "Recette de cuisine italienne"),
])
```

`link_objects` prend des paires `(id, texte)` — provenant indifféremment
d'un `CaseNode.label`, d'un `KnowledgeNode.label`, ou d'un
`KnowledgeObject.title` cabinet — les embed en un seul appel à
`EmbeddingProviderPort.embed()` (par défaut `HashingEmbeddingProvider`,
la même adaptée dans tout le reste de TMIS), puis calcule la
`cosine_similarity` (`tmis.ai.embeddings.similarity`) de chaque paire.
Seules les paires au-dessus de `similarity_threshold` deviennent un
`SemanticLink` persisté — un `SemanticLink` est pensé comme une
recommandation, pas un score brut pour toutes les paires possibles.

## Un `SemanticLink` n'est pas un edge de graphe

`SemanticLink(source_id, target_id, score, embedding_name)` est un
type à part, distinct de `CaseEdge`/`KnowledgeEdge`/`KnowledgeRelation`.
Les deux peuvent coexister entre la même paire d'ids sans conflit : un
`CaseEdge(relation="mentioned_in")` dit "ces deux objets sont reliés
dans le dossier" ; un `SemanticLink(score=0.91)` dit "ces deux objets
se lisent de façon similaire", indépendamment de tout lien explicite.

## Consulter les liens d'un objet

```python
engine.links_for("playbook-1")  # -> tous les SemanticLink touchant cet id
```

## Ce que ce module ne fait pas

- Il ne fournit pas de nouveau modèle d'embedding — `EmbeddingProviderPort`
  et `HashingEmbeddingProvider` restent ceux de `tmis.ai.embeddings`.
- Il ne construit pas de nouvel index vectoriel — la comparaison se
  fait en mémoire, sur les vecteurs déjà calculés pour l'appel
  (`link_objects` ne persiste jamais les vecteurs eux-mêmes, seulement
  le score et les ids).
- Il ne remplace pas `tmis.ai.rag` pour la recherche documentaire — ce
  module produit des relations *entre objets de connaissance*, pas des
  résultats de recherche pour une requête utilisateur.
