# Guide de la Clause Library (Sprint 12)

## Rôle

`tmis.cabinet_knowledge.clauses` mémorise les clauses type d'un
cabinet — non-concurrence, confidentialité, garantie, résiliation... —
avec leurs variantes, leurs commentaires, la jurisprudence associée et
un système de recherche avancée.

## Modèle

```python
Clause(id, domain: LegalDomain, clause_type, title,
       variants: tuple[ClauseVariant, ...],
       comments: tuple[str, ...], jurisprudence_refs: tuple[str, ...])
ClauseVariant(id, text, notes, language="fr")
```

Une `Clause` est un `KnowledgeObject` de type `CLAUSE`. L'historique et
le niveau de validation d'une clause ne sont **pas** dupliqués dans le
schéma `Clause` — ils sont déjà fournis par `governance/` et
`lineage/`, accessibles via l'objet sous-jacent
(`GET /cabinet-knowledge/objects/{id}/history`).

## Utilisation

```python
clauses = get_clause_engine()

clause = clauses.create_clause(
    firm_id, "Non-concurrence", LegalDomain.COMMERCIAL, "non_concurrence",
    variants=(ClauseVariant(id="v1", text="Interdiction de concurrence pendant 2 ans"),),
    author="avocat1",
)

# Ajouter une variante — passe par KnowledgeSpace.update_content(), donc
# repasse l'objet en DRAFT : une nouvelle validation est nécessaire
clauses.add_variant(firm_id, clause.id, ClauseVariant(id="v2", text="..."), actor="avocat1")

# Recherche avancée
clauses.search(firm_id, domain=LegalDomain.COMMERCIAL, clause_type="non_concurrence")
clauses.search(firm_id, keyword="concurrence")
```

`get_clause(firm_id, id, mark_used=True)` incrémente
`KnowledgeSpace.record_usage()` — utilisé quand une clause est
effectivement injectée dans un brouillon, pas lors d'une simple
consultation.

## Recherche : spécifique aux clauses vs. recherche générale

`ClauseEngine.search()` est une commodité filtrée (domaine, type,
mot-clé) propre aux clauses. `tmis.cabinet_knowledge.search.SearchEngine`
couvre, lui, tous les types de connaissance (voir
docs/60-guide-knowledge-space.md) — les deux coexistent
délibérément : la recherche de clauses a des critères propres
(domaine juridique, type de clause) qui n'ont pas de sens pour un
playbook ou un pattern de raisonnement.

## API

| Endpoint | Rôle |
|---|---|
| `POST /cabinet-knowledge/clauses` | créer (statut `DRAFT`) |
| `GET /cabinet-knowledge/clauses` | recherche (`domain`, `clause_type`, `keyword`) |
| `GET /cabinet-knowledge/clauses/{id}` | détail (marque une réutilisation) |
