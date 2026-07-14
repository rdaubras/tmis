# Rapport d'audit initial — Sprint 26 (Module Document + Persistance)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« Phase 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), ce qui
existe déjà pour les 7 domaines à persister et pour le socle DB/Celery,
et signale les deux écarts trouvés avec les prémisses du prompt — comme
demandé, l'implémentation s'est arrêtée sur ces deux points le temps
d'un arbitrage explicite avec l'utilisateur avant d'écrire une ligne de
code.

## Composants réutilisés tels quels

| Composant existant | Ce qu'il fournit déjà | Usage dans le Sprint 26 |
|---|---|---|
| `document_intelligence.storage.ports.DocumentStorePort` | `save`/`get`/`list_ids`, forme exacte confirmée par lecture | Implémenté par `SQLAlchemyDocumentStore`, signature inchangée |
| `document_intelligence.schemas.record.DocumentRecord` | Dataclass complet (bytes, OCR, layout, classification, métadonnées, entités, chronologie, chunk ids, warnings) | Colonnes du modèle SQLAlchemy en miroir exact |
| `document_intelligence.storage.in_memory_store.InMemoryDocumentStore` | Défaut dev/tests | Conservé sans modification |
| `case_intelligence.cases.ports.CaseStorePort` | `get`/`save`/`get_or_create`/`list_ids` | Implémenté par `SQLAlchemyCaseStore` |
| `case_intelligence.cases.schemas.CaseProfile` | Dataclass complet (acteurs, faits, preuves, chronologie, tâches, historique IA) | Colonnes en miroir |
| `case_intelligence.cases.in_memory_store.InMemoryCaseStore` | Défaut dev/tests | Conservé |
| `legal_research.history.ports.ResearchHistoryPort` | `record` (append-only)/`list_for_user`/`list_for_case`/`list_all` | Implémenté par `SQLAlchemyResearchHistory` |
| `legal_research.history.schemas.ResearchHistoryEntry` | Dataclass gelé, plat | Colonnes + un payload JSON |
| `legal_research.history.in_memory_history.InMemoryResearchHistory` | Défaut dev/tests | Conservé |
| `legal_drafting.documents.ports.DocumentStorePort` (brouillons) | `get`/`save`/`list_ids` | Implémenté par `SQLAlchemyDraftDocumentStore` (nom distinct de celui de `document_intelligence` pour éviter toute confusion de lecture) |
| `legal_drafting.documents.schemas.Document` | Dataclass complet (sections, citations, relecture, `is_draft` toujours `True`) | Colonnes en miroir ; `is_draft` reste une `@property` calculée, jamais stockée |
| `legal_drafting.documents.store.InMemoryDocumentStore` | Défaut dev/tests | Conservé |
| `collaboration.workspace.ports.WorkspaceStorePort` | `get`/`save`/`list_for_firm`/`list_ids` | Implémenté par `SQLAlchemyWorkspaceStore` |
| `collaboration.workspace.schemas.Workspace`/`WorkspaceSettings` | Dataclasses complets | Colonnes en miroir |
| `collaboration.workspace.store.InMemoryWorkspaceStore` | Défaut dev/tests | Conservé |
| `cabinet_knowledge.knowledge.ports.KnowledgeStorePort` | `save`/`get`/`list_for_firm(firm_id, type_=None)` | Implémenté par `SQLAlchemyKnowledgeStore` |
| `cabinet_knowledge.knowledge.schemas.KnowledgeObject` | Dataclass complet (`content: dict[str, Any]` déjà libre) | Colonnes en miroir |
| `cabinet_knowledge.knowledge.store.InMemoryKnowledgeStore` | Défaut dev/tests | Conservé |
| `tmis.core.config.Settings`/`get_settings()` | `database_url`, `redis_url` déjà configurés (préfixe d'env `TMIS_`) | Seule source de configuration lue par `core.db.session` et `core.tasks.celery_app` — aucune seconde config |
| `backend/alembic.ini`/`alembic/env.py` | Configuration Alembic déjà présente, migrations vides | Réutilisée telle quelle ; `env.py` étendu d'une ligne d'import par domaine (voir plus bas) |
| `document_intelligence.pipeline.DocumentIntelligencePipeline` (Sprint 3) | Pipeline complet, `async def process(...)`, déjà injectable via `document_store: DocumentStorePort` | Composé tel quel dans `core.tasks.document_tasks.process_document_task`, jamais reconstruit |
| `case_intelligence.workflow.CaseIntelligenceWorkflow` (Sprint 4) | `async def ingest_document(...)`, déjà injectable via `case_store`/`document_store` | Composé tel quel dans `core.tasks.case_tasks.trigger_case_workflow_task` |

## Composants étendus (changement additif, aucune rupture)

| Composant | Extension apportée | Pourquoi une extension et non un nouveau composant |
|---|---|---|
| `legal_reasoning.reasoner.ports` | Nouveau `SessionStorePort` (`get`/`save`/`list_ids`) | Ce port n'existait pas du tout avant ce sprint (voir « écart n°2 » ci-dessous) ; sa forme réplique exactement celle des 6 autres ports de ce sprint, pour rester cohérent avec la convention du dépôt |
| `legal_reasoning.reasoner.orchestrator.ReasoningOrchestrator` | Paramètre optionnel `session_store: SessionStorePort \| None = None`, défaut `InMemorySessionStore()` | Remplace le `dict` privé (`self._sessions`) à l'identique — `reason()`/`get_session()` gardent leur signature et leur comportement pour tout appelant existant qui ne fournit pas ce paramètre |
| `backend/alembic/env.py` | 7 lignes d'import (une par module d'adaptateur) pour enregistrer les modèles sur `Base.metadata` | Même patron que l'import déjà présent de `tmis.infrastructure.persistence.models` — aucune seconde façon d'enregistrer un modèle |
| `backend/pyproject.toml` | `asyncpg`, `python-multipart` en dépendances de production ; `aiosqlite` en dépendance de dev/tests ; `[[tool.mypy.overrides]]` pour `celery.*` (absence de stubs typés) | Nécessaires respectivement au moteur async (session.py), à l'endpoint d'upload multipart (FastAPI l'exige), aux tests d'intégration SQLite async, et à `mypy --strict` sur les tâches Celery |
| `tmis.api.v1.router` | Montage de `document_router` | Même patron que les 15 routers déjà montés |

## Composants réellement nouveaux (aucun équivalent trouvé)

| Nouveau composant | Justification |
|---|---|
| `tmis.core.db.base` | Aucun point d'import unique et documenté vers la `Base` partagée n'existait pour du code hors `infrastructure.persistence` — ce module ne déclare rien, il réexporte |
| `tmis.core.db.session` | Aucun moteur asyncpg n'existait dans le dépôt |
| `tmis.core.db.dataclass_json` | Aucun codec dataclass↔JSON générique n'existait ; sans lui, chaque store aurait réinventé sa propre (dé)sérialisation |
| `<domaine>/adapters/sqlalchemy_store.py` (7 fichiers, 2 en position frère `sqlalchemy_store.py` — voir écart n°3) | Aucune persistance réelle n'existait pour ces 7 entités |
| `tmis.core.tasks.celery_app` | Aucune application Celery n'était construite dans le dépôt (confirmé explicitement par le commentaire de `tmis.platform.health.bootstrap._check_queue`, qui renvoyait déjà vers ce sprint) |
| `tmis.core.tasks.document_tasks`/`case_tasks` | Aucune exécution asynchrone des pipelines DIE/CIE n'existait |
| `tmis.api.v1.document` (routes + schémas) | Aucun endpoint d'upload de document n'existait |
| 7 migrations Alembic (`0001_document_record` → `0007_knowledge_object`) | Le dossier `alembic/versions/` était vide (`.gitkeep` seul) |

## Écarts identifiés en Phase 0 — et comment ils ont été tranchés

Le prompt demandait explicitement de s'arrêter et de signaler tout écart
avec la forme attendue plutôt que de deviner. Deux écarts réels ont été
trouvés ; les deux ont été soumis à l'utilisateur (`AskUserQuestion`)
avant tout code, chacun avec plusieurs options tranchées explicitement.

### Écart n°1 — un modèle SQLAlchemy existait déjà

Le prompt affirmait qu'« aucun modèle SQLAlchemy n'existe actuellement
dans le dépôt ». Faux : `tmis.core.database.Base` (une
`DeclarativeBase`), `engine` (sync, `psycopg`) et `SessionLocal`
existaient déjà, avec `FirmModel`/`UserModel`/`CaseModel` et
`SqlAlchemyCaseRepository`/`SqlAlchemyFirmRepository` implémentant
`tmis.domain.case.ports.CaseRepositoryPort`/`tmis.domain.firm.ports.
FirmRepositoryPort` (socle identité/firm, bounded context distinct de
`case_intelligence.cases.CaseProfile` — donc pas un doublon du travail de
ce sprint, mais bien une `Base`/un moteur déjà là). `alembic/env.py`
importait déjà ces modèles.

**Décision retenue (utilisateur, option recommandée)** : `tmis.core.db.
base.Base` réexporte cette `Base` existante plutôt que d'en déclarer une
seconde ; `tmis.core.db.session` ajoute un moteur `asyncpg` à côté du
moteur sync existant, lisant la même configuration — un seul schéma de
référence, une seule chaîne de migrations, deux moteurs Python pour deux
usages distincts (voir docs/151-architecture-persistance.md).

### Écart n°2 — aucun port de stockage pour `ReasoningSession`

`legal_reasoning.reasoner.ports` ne contenait que des ports de
*consommation* (`ReasoningKernelPort`, `ReasoningCasePort`,
`ReasoningResearchPort`) — rien pour persister une `ReasoningSession`.
`ReasoningOrchestrator` la gardait dans un `dict` privé
(`self._sessions`), accessible seulement via `get_session()`.

**Décision retenue (utilisateur, option recommandée)** : ajouter un
nouveau `SessionStorePort` additif (même forme que les 6 autres ports de
ce sprint), un `InMemorySessionStore` qui remplace le `dict` privé à
l'identique, et un paramètre optionnel sur `ReasoningOrchestrator` —
zéro rupture pour tout appelant existant.

### Écart n°3 (mineur, résolu sans arbitrage utilisateur) — collision de nom de fichier

`legal_drafting.documents.adapters` et `legal_reasoning.reasoner.
adapters` existaient déjà comme **fichiers** `adapters.py` — un concept
sans rapport (adapter un port vers un autre moteur métier, ex.
`CaseIntelligenceCaseAdapter`), pas un sous-paquet. Impossible d'y créer
un sous-paquet `adapters/sqlalchemy_store.py` sans collision. Résolu en
plaçant ces deux stores en fichier frère (`sqlalchemy_store.py`), sans
toucher aux fichiers `adapters.py` existants — une décision mécanique de
nommage, pas un compromis d'architecture, donc pas soumise à arbitrage.

## Limite acceptée, documentée plutôt que corrigée

`case_intelligence.bootstrap.get_case_intelligence_workflow()` (Sprint 4)
continue de construire son `CaseIntelligenceWorkflow` avec
`InMemoryCaseStore` par défaut ; c'est ce câblage que les endpoints
`/api/v1/cases/*` utilisent. Le nouveau chemin asynchrone (`core.tasks.
case_tasks.trigger_case_workflow_task`) construit, lui, un
`CaseIntelligenceWorkflow` avec `SQLAlchemyCaseStore`. Changer le
câblage par défaut de `get_case_intelligence_workflow()` aurait un rayon
d'effet sur de nombreux tests d'intégration du Sprint 4 qui présument un
état en mémoire isolé par test — hors périmètre d'un sprint dont le
mandat est d'ajouter des adaptateurs derrière des ports existants, pas de
changer le câblage par défaut de singletons d'un sprint antérieur. Voir
docs/151-architecture-persistance.md.

## Conclusion

Le développement a pu commencer une fois les deux écarts ci-dessus
tranchés : chaque phase du sprint a un point de composition identifié
vers un port/composant existant, les deux extensions additives listées
plus haut sont suffisantes, et aucun nouveau composant proposé ne duplique
une capacité déjà présente dans le dépôt.
