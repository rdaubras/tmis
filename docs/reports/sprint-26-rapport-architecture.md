# Rapport d'architecture — Sprint 26 (Module Document + Persistance)

## Résumé

Le Sprint 26 ajoute une persistance Postgres réelle derrière les 7 ports
de stockage qui n'existaient qu'en mémoire (`document_intelligence`,
`case_intelligence`, `legal_research.history`, `legal_reasoning.reasoner`,
`legal_drafting.documents`, `collaboration.workspace`,
`cabinet_knowledge.knowledge`), un endpoint d'upload de document et une
exécution asynchrone via Celery. Le prompt exigeait une Phase 0 de
re-audit avant tout code ; cet audit
(docs/reports/sprint-26-rapport-audit.md) a trouvé deux écarts avec ses
prémisses (une `Base` SQLAlchemy existait déjà ; `legal_reasoning`
n'avait aucun port de stockage), chacun tranché explicitement avec
l'utilisateur avant d'écrire une ligne de code.

Périmètre livré : `backend/src/tmis/core/db/` (3 fichiers),
`backend/src/tmis/core/tasks/` (3 fichiers), 7 adaptateurs SQLAlchemy, 7
migrations Alembic chaînées, `backend/src/tmis/api/v1/document/` (2
fichiers), 49 tests d'intégration dédiés.

## Décisions structurantes

### Une seule `Base`, un seul moteur sync, un moteur async additionnel

`tmis.core.db.base.Base` réexporte `tmis.core.database.Base` (préexistant,
socle identité/firm) plutôt que d'en déclarer une seconde. Les 7 stores
SQLAlchemy de ce sprint utilisent le moteur **sync** déjà présent
(`tmis.core.database.engine`, `psycopg`), pour une raison structurelle et
non stylistique : les 7 ports qu'ils implémentent déclarent des méthodes
`def`, jamais `async def` — un `Protocol` ne peut pas changer de
signature, donc son implémentation ne peut pas devenir asynchrone. Le
moteur `asyncpg` ajouté par `tmis.core.db.session` sert exclusivement à
l'unique lecture de ce sprint qui n'a aucun port à respecter :
l'historique complet des versions d'un document
(`GET /documents/{id}/versions`, `DocumentStorePort.get()` n'exposant que
la dernière version par construction).

### Codec dataclass↔JSON générique, écrit une fois

`tmis.core.db.dataclass_json.to_json`/`from_json` sérialise/reconstruit
récursivement n'importe quel dataclass (imbriqué, `Enum`, `datetime`,
`uuid.UUID`, `set`/`frozenset`, `list`/`tuple`, `dict`, `X | None`) via
`dataclasses.fields()` + `typing.get_type_hints()`. Les 7 stores l'
utilisent identiquement : les champs qui doivent être indexables/filtrables
(`document_id`, `firm_id`, `case_id`, `type`...) obtiennent une colonne
dédiée, tout le reste part dans une seule colonne `payload` JSON. Sans ce
codec, chaque store aurait réimplémenté sa propre (dé)sérialisation pour
des dataclasses parfois profondément imbriquées (`ReasoningSession`
référence 9 schémas différents).

### Versionning : nouvelle ligne, jamais d'écrasement

Seul `document_records` (le domaine explicitement concerné par le
« Versionning des documents » du prompt) a une clé primaire de
substitution (`id`) distincte de la clé métier (`document_id`), avec
`version`/`previous_version_id`. Les 6 autres domaines n'ont aucune
exigence de versionning dans le prompt : leur `save()` est un upsert par
clé métier (`session.merge(...)`), qui reproduit exactement le
comportement d'écrasement des `InMemory*Store` existants
(`self._x[key] = value`).

### Exécution asynchrone : Celery pilote des coroutines, pas l'inverse

`DocumentIntelligencePipeline.process()` et `CaseIntelligenceWorkflow.
ingest_document()` (Sprints 3 et 4) sont déjà `async def`. Une tâche
Celery est un appelable synchrone ordinaire ; `core.tasks.document_tasks`/
`case_tasks` pilotent donc ces coroutines avec `asyncio.run()` à
l'intérieur d'une tâche synchrone — le patron correct pour un worker
Celery (process séparé, aucune boucle asyncio déjà active), documenté
dans le docstring des deux modules avec la mise en garde correspondante
pour les tests (voir plus bas).

### Deux stores nommés distinctement pour la même entité conceptuelle

`document_intelligence.storage.ports.DocumentStorePort` (documents
sources) et `legal_drafting.documents.ports.DocumentStorePort`
(brouillons) sont deux classes différentes dans deux modules différents,
mais partagent le même nom — un risque de confusion à la lecture, pas un
conflit Python. Le store SQLAlchemy du second s'appelle explicitement
`SQLAlchemyDraftDocumentStore` (jamais `SQLAlchemyDocumentStore`) pour
lever toute ambiguïté.

## Limite connue, assumée et documentée

`case_intelligence.bootstrap.get_case_intelligence_workflow()` (utilisé
par les endpoints synchrones `/api/v1/cases/*`) garde son câblage
`InMemoryCaseStore` par défaut, inchangé par ce sprint ; seul le nouveau
chemin asynchrone (`trigger_case_workflow_task`) utilise
`SQLAlchemyCaseStore`. Un dossier créé via l'API synchrone et un dossier
enrichi via l'upload asynchrone d'un document sont donc, pour l'instant,
deux vues qui ne convergent pas — voir
docs/151-architecture-persistance.md et le rapport d'audit pour la
justification du choix de ne pas élargir le périmètre du sprint à ce
câblage.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `core.db.base.Base` | `tmis.core.database.Base` (préexistant) | Une seconde base déclarative |
| `core.db.session` (moteur async) | `tmis.core.config.Settings.database_url` (préexistant) | Une seconde configuration DB |
| `core.tasks.celery_app` | `tmis.core.config.Settings.redis_url` (préexistant) | Une seconde configuration de file de tâches |
| `core.tasks.document_tasks.process_document_task` | `document_intelligence.pipeline.DocumentIntelligencePipeline` (S3) | Le pipeline DIE lui-même |
| `core.tasks.case_tasks.trigger_case_workflow_task` | `case_intelligence.workflow.CaseIntelligenceWorkflow` (S4) | Le workflow CIE lui-même |
| 7 `SQLAlchemy*Store` | Les 7 ports existants (Sprints 3-9), `core.db.base`/`.dataclass_json` | Les ports eux-mêmes, les `InMemory*Store` (conservés) |
| `api.v1.document` | `SQLAlchemyDocumentStore`, `process_document_task`, `AsyncSessionLocal` | Une logique de pipeline dans la couche API |

## Vérification finale

- `ruff check src alembic tests` → All checks passed
- `mypy src` (strict) → Success, aucune erreur
- `alembic history` / `upgrade head` / `downgrade base` (contre SQLite
  jetable) → chaîne linéaire `0001_document_record` → `0007_
  knowledge_object`, upgrade et downgrade propres
- `pytest` → 49 tests dédiés à ce sprint, tous passants (7 stores × ~7
  tests + 6 tests API/Celery), en plus de la suite préexistante

## Corrections apportées pendant la vérification

- `alembic/versions/0001_document_record.py` et
  `core/db/session.py` : imports non triés/ligne trop longue,
  corrigés par `ruff --fix` puis manuellement pour les deux
  `isinstance(x, (A, B))` → `isinstance(x, A | B)` (règle `UP038`).
- `tests/integration/legal_drafting/test_sqlalchemy_document_store.py`
  collisionnait de nom de module avec le test homonyme de
  `document_intelligence` (pytest sans paquets `__init__.py` exige des
  noms de fichier uniques) — renommé
  `test_sqlalchemy_draft_document_store.py`.
- `celery.*` n'a pas de stubs typés (`mypy --strict` échouait avec
  `import-untyped`) — ajout d'un `[[tool.mypy.overrides]]` ciblé, plus
  `# type: ignore[untyped-decorator]` sur les deux décorateurs
  `@celery_app.task(...)`, seul point du dépôt qui importe Celery.
- `python-multipart` manquait des dépendances (requis par FastAPI pour
  `UploadFile`/`Form`) — ajouté.
- Premier jet du test API : appeler `process_document_task.delay(...)`
  depuis un endpoint `async def` exécuté par `TestClient` (donc dans une
  boucle asyncio déjà active), avec Celery en mode eager, faisait
  échouer `asyncio.run()` à l'intérieur de la tâche
  (`cannot be called from a running event loop`) — un artefact de test,
  pas un bug de production (un worker Celery réel n'a pas de boucle
  active). Résolu en distinguant les tests qui vérifient l'endpoint
  (`.delay` intercepté) des tests qui vérifient la tâche elle-même
  (appelée directement, comme le ferait un worker).
