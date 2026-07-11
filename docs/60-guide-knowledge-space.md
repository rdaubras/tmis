# Guide du Knowledge Space (Sprint 12)

## Rôle

`tmis.cabinet_knowledge.knowledge.engine.KnowledgeSpace` est l'unique
point d'entrée sur la connaissance d'un cabinet — tous les autres
sous-modules de `cabinet_knowledge` lisent et écrivent au travers de
cette façade plutôt que de toucher directement
`KnowledgeStorePort`/`InMemoryKnowledgeStore`.

## Le modèle générique `KnowledgeObject`

| Champ | Rôle |
|---|---|
| `id` | identifiant unique (`know-<uuid>`) |
| `firm_id` | cabinet propriétaire — isolation stricte |
| `type` | `KnowledgeType` (playbook, clause, template, reasoning_pattern, writing_style, best_practice, lesson_learned, note, checklist, guide, internal_rule, jurisprudence_note, comment, decision) |
| `title` | titre lisible |
| `content` | payload libre (`dict`), sérialisé/désérialisé par le sous-module spécialisé |
| `author` | auteur de la création |
| `version` | incrémenté à chaque modification de contenu |
| `status` | `DRAFT` / `IN_REVIEW` / `VALIDATED` / `OBSOLETE` / `ARCHIVED` (voir docs/62-guide-gouvernance.md) |
| `quality_score` | calculé par `tmis.cabinet_knowledge.quality` |
| `tags` | ensemble de mots-clés/catégories (taxonomie, domaine...) |
| `is_published` | visibilité pour les agents (voir `approval/`) |
| `usage_count` | nombre de réutilisations réelles |

## Les sept opérations du Knowledge Space

```python
space = get_knowledge_space()

obj = space.create(firm_id, KnowledgeType.NOTE, "Titre", {"text": "..."}, author="avocat1")
space.get(firm_id, obj.id)                     # None si absent, TenantAccessError si autre cabinet
space.list(firm_id, type_=KnowledgeType.NOTE, status=KnowledgeStatus.VALIDATED)
space.update_content(firm_id, obj.id, {"text": "v2"}, actor="avocat1")   # → repasse en DRAFT
space.add_tags(firm_id, obj.id, frozenset({"rgpd"}))                     # métadonnée, pas de reset
space.set_quality_score(firm_id, obj.id, 0.82)                           # métadonnée, pas de reset
space.record_usage(firm_id, obj.id)                                      # une vraie réutilisation
```

`update_content` est la seule opération qui **remet un objet en
`DRAFT`** — toute autre écriture (tags, score qualité) est traitée
comme de la métadonnée et ne remet jamais en cause une validation déjà
obtenue.

## Isolation stricte

`space.get(firm_a, objet_du_firm_b)` lève
`tmis.platform.security.tenant_isolation.TenantAccessError` — jamais
un `None` silencieux, pour qu'une vérification manquante ailleurs ne
puisse pas être confondue avec "objet introuvable". `space.list()`
est nativement scopée par `firm_id`.

## Pourquoi un modèle générique plutôt que sept agrégats

Voir docs/59-architecture-cabinet-knowledge-engine.md — "Décision
structurante : un modèle générique, pas 12 tables". En résumé : la
mécanique de versionnement, de gouvernance et d'isolation est écrite
une seule fois ; chaque type de connaissance (playbook, clause,
template...) n'ajoute que sa vue typée et sa logique métier propre.

## API générique

- `POST /cabinet-knowledge/objects` — création directe (utile pour
  les types `NOTE`/`CHECKLIST`/`GUIDE`/`INTERNAL_RULE`/
  `JURISPRUDENCE_NOTE`/`COMMENT`/`DECISION` qui n'ont pas de moteur
  spécialisé dédié).
- `GET /cabinet-knowledge/objects/{id}` / `GET /cabinet-knowledge/objects`
- `GET /cabinet-knowledge/objects/{id}/history` — voir
  docs/62-guide-gouvernance.md
- `GET /cabinet-knowledge/objects/{id}/lineage` — traçabilité complète
- `POST /cabinet-knowledge/objects/{id}/quality` — calcule et persiste
  le score qualité
