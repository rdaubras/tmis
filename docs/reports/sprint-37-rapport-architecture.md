# Rapport d'architecture — Sprint 37 (Nettoyage + consolidation DocumentStorePort)

## Résumé

Le Sprint 37 est un sprint de plomberie interne en deux parties
indépendantes, sans nouvelle fonctionnalité et sans agent touché dans sa
logique métier.

**Partie A** supprime `backend/uv.lock` (4308 lignes, mergé hors scope au
Sprint 36), confirmé référencé par aucun processus du dépôt
(`docs/reports/sprint-37-rapport-audit.md`).

**Partie B** consolide `DocumentStorePort` : trois composition roots
construisaient chacun leur propre store par défaut, retombant sur
`InMemoryDocumentStore()` plutôt que sur `SQLAlchemyDocumentStore`
(l'implémentation Postgres livrée au Sprint 26) — alors qu'un quatrième
point d'entrée, `process_document_task` (le flux réel d'upload),
construisait déjà le bon store depuis onze sprints. Un singleton
`@lru_cache`, `document_intelligence.bootstrap.get_document_store()`,
suit le patron déjà établi par `legal_research.bootstrap.
get_research_orchestrator()`/`cabinet_knowledge.bootstrap.
get_knowledge_space()` et est désormais injecté dans les trois points
d'entrée qui en manquaient.

Périmètre livré : `document_intelligence/bootstrap.py` (ajout de
`get_document_store()`, `get_document_pipeline()` alimenté),
`agents/orchestrator.py` (l'`AnalysisAgent` par défaut de `Orchestrator`
alimenté), `agents/bootstrap.py` (`get_contract_agent()` alimenté),
`api/v1/document/routes.py` (`get_document_store()` local supprimé, pointe
vers le singleton partagé), 4 tests unitaires nouveaux, 2 fichiers de test
d'intégration existants adaptés (fixture d'environnement uniquement,
aucune assertion changée), `docs/151-architecture-persistance.md`,
`docs/09-roadmap-30-sprints.md`.

**`process_document_task` non modifié. Aucune signature de
`DocumentStorePort`, `AnalysisAgent`, `ContractAgent` ou
`DocumentIntelligencePipeline` modifiée. Aucun agent exposé côté API.**

## Décisions structurantes

### `get_document_store()` : même patron `@lru_cache` que les composition roots déjà en place

```python
# document_intelligence/bootstrap.py
@lru_cache
def get_document_store() -> DocumentStorePort:
    return SQLAlchemyDocumentStore()
```

Contrairement aux connecteurs LRE (`legal_research.connectors.factory`,
réel HTTP vs. fixture — un choix de configuration explicite), il n'existe
aucune branche réel/fixture à ce niveau pour `DocumentStorePort` :
`SQLAlchemyDocumentStore` est toujours l'implémentation de production
(elle lit `Settings.database_url` directement), et
`InMemoryDocumentStore` reste le défaut de chaque constructeur d'agent
quand rien n'est injecté (tests, ou tout appelant qui choisit
explicitement de ne pas utiliser Postgres). Le singleton ne fait donc
aucun choix — il retourne toujours la même implémentation, comme
`get_research_orchestrator()` retourne toujours le même
`ResearchOrchestrator` construit une fois pour tout le process.

La construction de `SQLAlchemyDocumentStore()` reste **paresseuse** : son
constructeur ne fait qu'enregistrer `session_factory: Callable[[],
Session] = SessionLocal` (Sprint 26) — aucune connexion n'est ouverte
avant le premier appel réel à `save()`/`get()`/`list_ids()`. Le singleton
est donc sûr à instancier même dans un test qui ne finit jamais par
toucher réellement le document store (voir plus bas, `Orchestrator()` /
`AnalysisAgent()`/`ContractAgent()` bare dans les tests existants).

### Les trois points d'entrée qui construisaient leur propre store par défaut

```python
# document_intelligence/bootstrap.py
@lru_cache
def get_document_pipeline() -> DocumentIntelligencePipeline:
    return DocumentIntelligencePipeline(
        event_bus=get_kernel().event_bus, document_store=get_document_store()
    )
```

```python
# agents/orchestrator.py
self._analysis_agent = analysis_agent or AnalysisAgent(document_store=get_document_store())
```

```python
# agents/bootstrap.py
@lru_cache
def get_contract_agent() -> ContractAgent:
    return ContractAgent(
        kernel=get_kernel(),
        document_store=get_document_store(),
        case_store=get_case_intelligence_workflow().case_store,
        clause_engine=get_clause_engine(),
        fabric=get_ai_intelligence_fabric(),
        governance=get_ai_governance_platform(),
    )
```

Dans les trois cas, seul l'appelant change ce qu'il passe au constructeur
existant — `document_store: DocumentStorePort | None = None` n'a changé
de forme dans aucun des trois constructeurs (`DocumentIntelligencePipeline`,
`AnalysisAgent`, `ContractAgent`). Un test qui injecte encore
explicitement `InMemoryDocumentStore()` (tous les tests unitaires
d'agents existants, `test_pipeline_*` sur `DocumentIntelligencePipeline`)
continue de le faire sans aucun changement de comportement.

### `api/v1/document/routes.py` : la définition locale devient une délégation

Avant (Sprint 26 Phase 4) :

```python
def get_document_store() -> SQLAlchemyDocumentStore:
    return SQLAlchemyDocumentStore()
```

Après :

```python
from tmis.document_intelligence.bootstrap import get_document_store
```

Le comportement observable de l'API ne change pas (`SQLAlchemyDocumentStore`
avant, `SQLAlchemyDocumentStore` — via le singleton — après) ; ce qui
change est que ce router ne construit plus sa propre instance
indépendante mais partage désormais la même que le pipeline et les deux
agents, comme demandé par la mission.

### `process_document_task` confirmé correct, non touché

`core.tasks.document_tasks.process_document_task` construisait déjà
`SQLAlchemyDocumentStore()` directement, sans passer par un composition
root (voir son propre docstring, inchangé : « The API endpoint persists
the initial ... `DocumentRecord` via `SQLAlchemyDocumentStore`
synchronously ... then enqueues this task »). Ce sprint ne l'a pas fait
passer par `get_document_store()` : la mission l'exige explicitement
(« CORRECT AUJOURD'HUI ... Ce flux réel d'upload fonctionne déjà
correctement ; ne pas le casser »), et le faire aurait élargi le
périmètre sans bénéfice — cette tâche Celery construit son store une
seule fois par exécution de tâche, jamais en boucle chaude, donc le
partage d'instance n'y apporte rien que `SQLAlchemyDocumentStore()`
n'offre déjà (une connexion lazy vers la même base). `git diff --stat`
sur `tmis/core/tasks/document_tasks.py` est vide.

### Conséquence sur `tests/integration/case_intelligence/test_case_api.py`

Trois tests de ce fichier appellent `get_document_pipeline()` puis
`pipeline.process(...)` sans jamais injecter de store explicite — ils
dépendaient donc implicitement de l'ancien défaut en mémoire du pipeline,
pas d'une injection explicite protégée par la règle non négociable de la
mission. Une fois `get_document_pipeline()` alimenté par le singleton
`SQLAlchemyDocumentStore` partagé, ces tests auraient tenté une vraie
connexion Postgres. Correction : le même patron déjà utilisé par
`tests/integration/document_intelligence/test_document_upload_api.py`
(Sprint 26 Phase 4), un fixture `autouse` qui reconfigure le
`SessionLocal` synchrone process-wide sur une base sqlite jetable avant
chaque test :

```python
sync_engine = create_engine(
    f"sqlite:///{tmp_path}/sprint37-case-api.db",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
core_db_base.Base.metadata.create_all(
    sync_engine, tables=[core_db_base.Base.metadata.tables["document_records"]]
)
core_db_session.SessionLocal.configure(bind=sync_engine)
```

`SQLAlchemyDocumentStore` ne capture jamais l'engine à la construction —
seulement une référence au `sessionmaker` (`SessionLocal`, Sprint 26,
`tmis.core.db.session`) — donc reconfigurer ce sessionmaker avant le test
suffit à rediriger toute instance existante ou future, y compris une
instance déjà mise en cache par `get_document_store()` d'un test
précédent. `get_document_store.cache_clear()` est tout de même appelé,
comme les deux autres singletons de ce fixture, pour rester cohérent avec
le reste du patron de test du dépôt (chaque singleton touché est
explicitement réinitialisé), même si ce n'est pas strictement nécessaire
à la correction du test. **Aucune assertion de ce fichier n'a changé.**

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `document_intelligence.bootstrap.get_document_store` | `SQLAlchemyDocumentStore` (Sprint 26, inchangé) | Un second adaptateur de persistance, un second moteur de base de données |
| `get_document_pipeline()` (étendu) | `get_document_store()` (nouveau) + `get_kernel().event_bus` (inchangé) | Un second `DocumentStorePort` |
| `Orchestrator.__init__` (étendu) | `get_document_store()` (nouveau) | Un second store pour `AnalysisAgent` |
| `agents.bootstrap.get_contract_agent` (étendu) | `get_document_store()` (nouveau), tout le reste inchangé | Un second store pour `ContractAgent` |
| `api.v1.document.routes.get_document_store` | `document_intelligence.bootstrap.get_document_store()` (nouveau) | Une seconde instance de `SQLAlchemyDocumentStore` |

## Tests

- `tests/unit/document_intelligence/test_bootstrap.py` (+4, nouveau
  fichier) : `get_document_store()` est un singleton (`is` sur deux
  appels) ; `get_document_pipeline().document_store`,
  `get_contract_agent()._document_store` et
  `Orchestrator()._analysis_agent._document_store` sont tous trois la
  même instance que `get_document_store()`.
- `tests/integration/case_intelligence/test_case_api.py` : fixture
  d'environnement adaptée (sqlite jetable pour `SessionLocal`), zéro
  assertion modifiée — voir « Conséquence... » ci-dessus.
- `tests/integration/document_intelligence/test_document_upload_api.py` :
  `get_document_store.cache_clear()` ajouté au fixture existant, par
  cohérence avec le reste du patron de réinitialisation des singletons —
  aucun changement de comportement (ce fichier reconfigurait déjà
  `SessionLocal` sur sqlite avant ce sprint).
- Aucun test unitaire d'agent (`test_analysis_agent.py`,
  `test_contract_agent.py`) modifié : tous injectent déjà
  `InMemoryDocumentStore()` explicitement là où un document est
  réellement lu, ou n'atteignent jamais `self._document_store` (chemin
  « pas de `document_id` »).

## Vérification finale

- `pytest -q` (depuis `backend/`) → **2187 passed, 7 skipped** (2183
  tests préexistants + 4 nouveaux, 0 régression ; les 7 `skipped` sont
  préexistants, gatés par `TMIS_REDIS_URL`/
  `TMIS_RUN_MODEL_DOWNLOAD_TESTS`, non liés à ce sprint).
- `ruff check src tests` (commande CI) → **All checks passed**.
- `mypy src` (commande CI, mode strict) → **Success: no issues found in
  1896 source files**.
- `backend/uv.lock` : supprimé (`git rm`), confirmé absent de tout
  processus du dépôt avant suppression (voir rapport d'audit).
- `process_document_task` : `git diff --stat` sur
  `tmis/core/tasks/document_tasks.py` est vide — non touché.
- `DocumentStorePort`, `AnalysisAgent.__init__`, `ContractAgent.__init__`,
  `DocumentIntelligencePipeline.__init__` : `git diff` ne montre aucune
  ligne modifiée dans aucun de ces quatre — seules leurs valeurs par
  défaut d'appel, jamais leurs signatures, ont changé côté appelant.
