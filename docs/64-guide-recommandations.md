# Guide des Recommandations (Sprint 12)

## Rôle

`tmis.cabinet_knowledge.recommendations` propose automatiquement des
clauses, modèles, playbooks, checklists ou toute autre connaissance
pertinente pour un contexte donné (domaine juridique, mots-clés). Une
recommandation n'est **jamais une boîte noire** : chaque résultat
porte une explication lisible.

## Ce qui peut être recommandé

Uniquement les connaissances **validées et publiées**
(`status == VALIDATED` et `is_published == True`) — un brouillon,
même excellent, n'est jamais recommandé : voir docs/62-guide-gouvernance.md.

```python
recommendations = get_recommendation_engine()

recs = recommendations.recommend(
    firm_id,
    RecommendationContext(domain_tag="commercial", keywords=("concurrence",)),
    limit=5,
)
for r in recs:
    print(r.title, r.score, r.explanation)
```

## Comment le score est calculé

```
score = (part des mots-clés du contexte trouvés dans le titre/contenu) * 0.5
      + quality_score de l'objet * 0.5
```

Si des mots-clés sont fournis et qu'aucun ne correspond, l'objet est
exclu (pas de recommandation "à tout hasard"). Sans mots-clés ni
domaine, toutes les connaissances publiées du domaine sont retournées,
triées par score de qualité seul.

## Explicabilité (contrainte du sprint)

Chaque `Recommendation.explanation` est construite à partir des
critères réellement satisfaits — jamais un texte générique :

- `"correspond au domaine « commercial »"` si `domain_tag` a filtré ;
- `"mots-clés en commun : concurrence"` si des mots-clés ont matché ;
- `"qualité évaluée à 0.82"` si l'objet a un score de qualité connu.

Une recommandation sans aucun de ces trois signaux affiche
`"connaissance publiée du cabinet"` plutôt que de rester vide — il n'y
a jamais de recommandation sans justification.

## Réutilisation comptabilisée

Contrairement à une simple recherche (`tmis.cabinet_knowledge.search`,
qui ne touche jamais `usage_count`), chaque connaissance retournée par
`recommend()` déclenche `KnowledgeSpace.record_usage()` — être
recommandé et effectivement présenté à un juriste compte comme une
réutilisation pour le calcul de qualité et les statistiques
d'évaluation du cabinet.

## API

```
POST /cabinet-knowledge/recommendations
{ "firm_id": "...", "domain_tag": "commercial", "keywords": ["concurrence"], "limit": 5 }
```

Réponse : liste de `{ knowledge_object_id, object_type, title, score, explanation }`.
