# Rapport d'architecture — Sprint 12 (Cabinet Knowledge Engine)

## Résumé

Le Sprint 12 ajoute `backend/src/tmis/cabinet_knowledge/` (18
sous-modules + une couche API) au-dessus du socle existant. Aucun
module métier des Sprints 2-11 n'a été modifié ; seuls
`tmis/api/v1/router.py` (branchement du routeur) ont été touchés hors
`cabinet_knowledge/`, et `tmis.legal_drafting.templates.schemas.
DocumentType` (Sprint 7) est réutilisé en lecture seule par
`templates/`.

## Conformité aux principes architecturaux

- **Clean Architecture / DDD / SOLID** : chaque module suit le même
  patron que les sprints précédents — `schemas.py` → `ports.py`
  (quand une persistance dédiée existe) → implémentation(s) →
  composition dans `cabinet_knowledge/bootstrap.py`.
- **Event Driven Architecture** : chaque enrichissement, validation,
  recherche et recommandation est journalisé de façon structurée
  (`structlog`) et publié comme métrique Prometheus
  (`tmis.platform.metrics`), prêt à être republié comme évènement de
  domaine dans un sprint ultérieur — même approche que le Sprint 11.
- **Isolation stricte par tenant** : `KnowledgeSpace` est l'unique
  point d'accès au store et réutilise
  `tmis.platform.security.tenant_isolation` (Sprint 10) — une lecture
  cross-cabinet lève `TenantAccessError` plutôt que de retourner
  silencieusement `None`. Vérifié par un test d'intégration dédié.
- **Validation humaine obligatoire** : vérifié architecturalement —
  aucune fonction de `cabinet_knowledge` ne peut faire passer un objet
  à `VALIDATED` en dehors de
  `tmis.cabinet_knowledge.validation.ValidationEngine.decide(APPROVE, ...)`.

## Décision structurante : un modèle générique plutôt que 7 agrégats dupliqués

Le sprint demande un modèle de connaissance "extensible" et sept
familles de contenu (playbooks, clauses, templates, patterns de
raisonnement, style rédactionnel, bonnes pratiques, retours
d'expérience). Plutôt que d'écrire sept agrégats et sept stores quasi
identiques, `tmis.cabinet_knowledge.knowledge.KnowledgeObject` est
**l'unique** agrégat persistant (`content: dict` libre), et chaque
module spécialisé n'ajoute que :

1. une vue fortement typée (`Playbook`, `Clause`, ...) ;
2. des fonctions `xxx_to_content()`/`xxx_from_knowledge_object()` ;
3. de la logique métier réelle (ex. `PlaybookEngine.start_instance()`
   + suivi de checklist, `ClauseEngine.search()` filtré).

Toute la mécanique de versionnement (`update_content` bumpe la
version et redescend en `DRAFT`), de gouvernance
(`ALLOWED_TRANSITIONS`), d'isolation (`require_same_firm`) et de
traçabilité (`LineageEngine`) est donc écrite une seule fois et
héritée par les sept types de connaissance — voir docs/59 pour le
détail.

## Décision structurante : validation et publication sont deux gestes humains distincts

Le sprint impose : *"Aucune connaissance ne peut être ajoutée
automatiquement sans validation humaine."* Deux mécanismes séparés
l'implémentent :

- `validation/` — un objet ne devient `VALIDATED` qu'après un appel
  explicite `decide(APPROVE, reviewer=...)`, jamais automatiquement.
- `approval/` — un objet `VALIDATED` n'est visible des agents
  (`search`/`recommendations`, filtre `published_only`) qu'après un
  second appel explicite `publish(approver=...)`. Toute sortie de
  `VALIDATED` (vers `OBSOLETE`/`ARCHIVED`) dépublie automatiquement
  l'objet (`KnowledgeSpace.set_status`), pour qu'une connaissance
  obsolète ne reste jamais visible par erreur.

## Autre décision : recherche passive vs. réutilisation comptée

`tmis.cabinet_knowledge.search.SearchEngine` ne touche jamais
`KnowledgeObject.usage_count` — parcourir des résultats de recherche
n'est pas une "réutilisation". Seuls les points de consommation réelle
(instanciation d'un playbook, récupération d'une clause avec
`mark_used=True`, une recommandation effectivement retournée)
incrémentent le compteur, qui alimente ensuite le score de qualité
(`quality/`, dimension "fréquence d'utilisation") et les statistiques
d'évaluation (`evaluation/`). Un test dédié
(`test_search_never_records_usage`) fige cette distinction.

## Réutilisation explicite des sprints précédents

- `tmis.platform.security.tenant_isolation` (Sprint 10) — isolation
  multi-cabinet, chokepoint unique dans `KnowledgeSpace.get()`.
- `tmis.platform.metrics`/`structlog` (Sprint 10) — observabilité,
  visible sur `/platform/metrics` aux côtés des métriques des sprints
  précédents.
- `tmis.legal_drafting.templates.schemas.DocumentType` (Sprint 7) —
  `templates/` référence les 9 types de documents existants au lieu
  de les redéfinir.

## Vérification de non-régression

`ruff check src tests` et `mypy src` : aucune erreur sur 856 fichiers
source (contre 776 avant ce sprint). `pytest` : **1068 tests passés, 4
ignorés** (contre 987 avant ce sprint) — 81 tests dédiés à
`cabinet_knowledge` (59 unitaires + 22 d'intégration), couverture
globale 95,78 %, sans qu'aucun des 987 tests précédents n'ait été
modifié.

## Ce que ce sprint ne fait pas (dette assumée)

- `reasoning_patterns/` n'est pas encore branché dans
  `tmis.legal_reasoning.ReasoningOrchestrator` (Sprint 6) — la
  bibliothèque existe et est interrogeable (`find_applicable`), mais
  son injection réelle dans un raisonnement reste un point
  d'intégration futur.
- `writing_style.apply_style()` reste une transformation déterministe
  (signature), pas une réécriture par un modèle.
- Le stockage reste en mémoire, aligné sur le calendrier de
  persistance générale de TMIS (Sprint 14, Module Document).

## Voir aussi

`docs/59-architecture-cabinet-knowledge-engine.md` pour les diagrammes
Mermaid détaillés (composition des modules, cycle de vie d'une
connaissance, pipeline complet). `docs/reports/sprint-12-demo.md` pour
la démonstration avec données fictives.
