# Guide : le système de citations du Legal Research Engine

Chaque `ResearchResult` renvoyé par le LRE peut être transformé en
`ResearchCitation` (`citations/schemas.py`) — les six champs que le
sprint promet de conserver pour toute source utilisée :

```python
@dataclass(frozen=True, slots=True)
class ResearchCitation:
    source_id: str
    title: str
    date: str | None
    document_type: str
    reference: str
    excerpt: str
```

`ResearchCitation` est distincte de `tmis.ai.schemas.citation.Citation`
(RAG générique du Kernel, Sprint 2, quatre champs) : le LRE a besoin de
davantage de traçabilité (type de document, date) pour des sources
juridiques que la citation RAG générique attachée à une réponse de
chat.

## Construire une citation

`citations.CitationEngine.build(result)` extrait les six champs
directement depuis un `ResearchResult` déjà normalisé — aucune
information supplémentaire n'est nécessaire, la normalisation
(`docs/21-legal-research.md`) a déjà unifié les métadonnées par
connecteur.

## Formats de sortie interchangeables

`citations.ports.CitationFormatterPort` définit un format de sortie ;
deux implémentations livrées avec le Sprint 5 :

| Formatter | Usage | Exemple |
|---|---|---|
| `PlainTextCitationFormatter` | ligne compacte, sortie chat/agent | `Code civil, article 1240 (1240, 1804-01-01)` |
| `FootnoteCitationFormatter` | note de bas de page, documents générés | `Code civil, article 1240, code, 1240, 1804-01-01 — « Tout fait... » [source: civ-1240]` |

```python
citation = CitationEngine().build(result)
CitationEngine().format(citation, FootnoteCitationFormatter())
```

## Ajouter un nouveau format

1. Implémenter `CitationFormatterPort` dans `citations/formatters.py`
   (ou un nouveau fichier) :

   ```python
   class OSCOLACitationFormatter:
       def format(self, citation: ResearchCitation) -> str:
           ...
   ```

2. L'utiliser via `CitationEngine.format(citation, OSCOLACitationFormatter())` —
   aucune modification de `CitationEngine`, de l'orchestrateur ou de
   l'API n'est nécessaire : le format est choisi par l'appelant au
   moment de l'affichage, pas figé dans le pipeline de recherche.

## Où les citations vivent dans la réponse

`ResearchOrchestrator.search()` construit une citation par résultat et
les garde en mémoire, indexées par `search_id`
(`get_citations(search_id)`), pour que `GET /legal-research/searches/{id}`
puisse les reconsulter sans relancer la recherche.
