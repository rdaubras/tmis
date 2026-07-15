# Rapport d'audit — Sprint 37 (Nettoyage + consolidation DocumentStorePort)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« PHASE 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), ce qui
existe déjà pour chacun des fichiers désignés par le prompt sur les deux
parties de la mission (nettoyage `uv.lock` et consolidation
`DocumentStorePort`), confirme qu'aucun n'a changé de forme depuis son
sprint d'origine, et documente une conséquence de la Partie B découverte
en cours d'audit : un test d'intégration existant dépendait implicitement
de l'ancien défaut en mémoire.

## Partie A — `backend/uv.lock` : confirmé non référencé

| Point vérifié | Résultat |
|---|---|
| `.github/workflows/ci.yml` | `pip install -e ".[dev,ci]"` — aucune mention de `uv` ni de `uv.lock` |
| `backend/Dockerfile` | `pip install --no-cache-dir .` — aucune mention de `uv` ni de `uv.lock` |
| `backend/README.md` | `pip install -e ".[dev]"` — aucune mention de `uv` ni de `uv.lock` |
| Recherche globale du dépôt (hors `.git/`) | Aucune autre référence à `uv.lock` |

Confirmé : le fichier (4308 lignes, mergé hors scope au Sprint 36 par le
commit « Add uv.lock for reproducible backend dependency resolution »)
n'est le produit d'aucune décision explicite de câblage CI/Dockerfile —
supprimé tel quel, sans aucun changement à `.github/workflows/ci.yml`,
`backend/Dockerfile` ni `backend/README.md`.

## Partie B — Fichiers désignés par le prompt : forme confirmée, aucun écart de contenu

| Fichier | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `document_intelligence.storage.ports.DocumentStorePort` | `Protocol` : `save(record)`, `get(document_id)`, `list_ids()` | Confirmé exact — **non modifié**, aucune signature touchée |
| `document_intelligence.adapters.sqlalchemy_store.SQLAlchemyDocumentStore` | Implémentation Postgres (Sprint 26), moteur sync, `session_factory: Callable[[], Session] = SessionLocal` par défaut | Confirmé exact — **non modifié** ; construction toujours paresseuse (aucune connexion tant que `save()`/`get()`/`list_ids()` n'est pas appelé), ce qui rend le singleton sûr à instancier même sans base de données joignable |
| `document_intelligence.storage.in_memory_store.InMemoryDocumentStore` | Implémentation par `dict` en mémoire | Confirmé exact — **non modifié**, reste le défaut de chaque agent/pipeline quand aucun `document_store` n'est injecté |
| `document_intelligence.bootstrap.get_document_pipeline` | `@lru_cache`, construisait `DocumentIntelligencePipeline(event_bus=get_kernel().event_bus)` **sans** `document_store` → défaut du pipeline, `InMemoryDocumentStore()` | Confirmé exact — écart avéré avec la production, corrigé par ce sprint |
| `document_intelligence.pipeline.document_pipeline.DocumentIntelligencePipeline` | `document_store: DocumentStorePort | None = None` déjà dans le constructeur, jamais alimenté par le bootstrap | Confirmé exact — **signature non modifiée**, seul l'appelant change |
| `core.tasks.document_tasks.process_document_task` | Construit `SQLAlchemyDocumentStore()` directement et l'injecte dans `DocumentIntelligencePipeline(document_store=...)`, sans passer par `get_document_pipeline()` | Confirmé exact — **CORRECT, non modifié** ; c'est le seul des quatre points d'entrée qui pointait déjà vers Postgres avant ce sprint |
| `api.v1.document.routes.get_document_store` | Fonction locale retournant `SQLAlchemyDocumentStore()`, redéfinie à chaque appel | Confirmé exact — comportement déjà correct (Postgres), mais dupliquait la construction plutôt que de partager un singleton |
| `agents.orchestrator.Orchestrator.__init__` | `self._analysis_agent = analysis_agent or AnalysisAgent()` — aucun `document_store` passé → défaut de l'agent, `InMemoryDocumentStore()` | Confirmé exact — écart avéré, corrigé par ce sprint |
| `agents.analysis_agent.AnalysisAgent.__init__` / `agents.contract_agent.ContractAgent.__init__` | `document_store: DocumentStorePort | None = None` déjà dans les deux constructeurs, jamais alimenté par un composition root partagé | Confirmé exact — **signatures non modifiées**, seuls les appelants changent |
| `agents.bootstrap.get_contract_agent` | `@lru_cache`, construisait `ContractAgent(kernel=..., case_store=..., clause_engine=..., fabric=..., governance=...)` **sans** `document_store` → défaut de l'agent, `InMemoryDocumentStore()` (le docstring le disait explicitement : « no shared document store singleton exists in this composition root yet ») | Confirmé exact — écart avéré, corrigé par ce sprint |
| `legal_research.bootstrap.get_research_orchestrator` / `cabinet_knowledge.bootstrap.get_knowledge_space` | Patron de référence : `@lru_cache` sur une fonction `get_xxx()` qui construit l'implémentation réelle une seule fois pour tout le process | Confirmé exact — patron reproduit à l'identique pour `get_document_store()` |

Aucun de ces fichiers n'avait un contenu différent de celui attendu par
la mission.

## Découverte en cours d'audit : un test d'intégration dépendait implicitement de l'ancien défaut en mémoire

La mission interdit explicitement de changer le comportement des tests
qui **injectent déjà `InMemoryDocumentStore()` explicitement**, mais
autorise (et attend) que le comportement *par défaut* change. Un
recensement de tous les appels à `AnalysisAgent()`/`ContractAgent()`/
`Orchestrator()`/`get_document_pipeline()` sans store explicite a
confirmé :

- `tests/unit/test_orchestrator.py::test_orchestrator_runs_analysis_then_verifier`
  (`Orchestrator()` bare) et
  `tests/unit/agents/test_analysis_agent.py::test_analysis_agent_without_document_id_is_low_confidence` /
  `tests/unit/agents/test_contract_agent.py::test_contract_agent_without_document_id_is_low_confidence`
  (`AnalysisAgent()`/`ContractAgent()` bare) : **aucun impact**. Les
  trois exercent le chemin « pas de `document_id` dans le contexte »,
  qui retourne avant tout appel à `self._document_store`, donc avant
  qu'un store Postgres construit paresseusement ne touche jamais une
  connexion.
- `tests/integration/case_intelligence/test_case_api.py` : **impact
  réel**. Trois tests (`test_get_profile_reflects_documents_processed_
  for_the_case`, `test_timeline_endpoint_returns_consolidated_entries`,
  `test_search_endpoint_finds_indexed_facts`) appellent
  `get_document_pipeline()` puis `pipeline.process(...)`, en s'appuyant
  implicitement sur le défaut en mémoire du pipeline pour que
  `document_store.save()` réussisse sans base de données réelle. Une
  fois `get_document_pipeline()` alimenté par le singleton
  `SQLAlchemyDocumentStore` partagé, ces trois tests auraient tenté une
  vraie connexion Postgres (`Settings.database_url`, par défaut
  `postgresql+psycopg://tmis:tmis@localhost:5432/tmis`) — absente de cet
  environnement d'exécution, et non préparée par une étape de migration
  dans `.github/workflows/ci.yml` même quand le service `postgres` de CI
  est disponible.

**Décision** : ce fichier de test n'injectait pas explicitement
`InMemoryDocumentStore()` — il dépendait du défaut implicite, que la
mission autorise justement à changer. La règle « tous les tests
existants doivent rester verts » est donc satisfaite en donnant à ce
fichier le même patron déjà utilisé par
`tests/integration/document_intelligence/test_document_upload_api.py`
(Sprint 26 Phase 4) : reconfigurer le `SessionLocal` synchrone
process-wide sur une base sqlite jetable (fichier temporaire,
`create_all` restreint à la table `document_records`) dans un fixture
`autouse`, plutôt que de laisser le test toucher la vraie
`TMIS_DATABASE_URL`. Aucune assertion du test n'a changé — uniquement
son fixture d'environnement. Voir
`docs/reports/sprint-37-rapport-architecture.md` pour le diff exact.

## Confirmation explicite : aucune signature de port ni d'agent modifiée

- `DocumentStorePort` : **aucune ligne modifiée**.
- `AnalysisAgent`, `ContractAgent` : **aucune ligne modifiée** — les deux
  avaient déjà `document_store: DocumentStorePort | None = None` dans
  leur constructeur ; seuls les appelants (`Orchestrator`,
  `get_contract_agent()`) changent ce qu'ils y passent par défaut.
- `DocumentIntelligencePipeline` : **aucune ligne modifiée** — même
  constat, seul `get_document_pipeline()` change ce qu'il lui passe.
- `process_document_task` : **aucune ligne modifiée** — déjà correct,
  confirmé par lecture directe avant tout code, jamais touché.
- `SQLAlchemyDocumentStore`, `InMemoryDocumentStore` : **aucune ligne
  modifiée**.
- Aucun agent n'a été exposé côté API dans ce sprint — l'exposition des
  agents (research/jurisprudence/contract/watch/orchestrator) reste hors
  périmètre, comme l'exige la mission.

## Conclusion

Aucun des fichiers désignés par le prompt n'avait un contenu différent de
celui attendu. La cartographie fournie par la mission (Phase 0) est
confirmée exacte de bout en bout. Un seul écart de comportement de test a
été identifié en cours d'audit — un test d'intégration qui dépendait
implicitement, et non explicitement, de l'ancien défaut en mémoire — et
corrigé sans toucher à ses assertions, conformément à la règle non
négociable qui ne protège que l'injection explicite
d'`InMemoryDocumentStore()`.
