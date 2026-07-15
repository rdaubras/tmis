# Rapport d'audit — Sprint 41 (Consolidation + Exposition d'`Orchestrator`)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« PHASE 0 — Re-audit avant code », répétée pour
chacune des deux parties). Il recense, par lecture directe du code (jamais
par déduction depuis les noms), l'état réel des fichiers désignés par la
mission, confirme qu'aucun n'a changé de forme depuis son sprint
d'origine, documente le raisonnement derrière les questions ouvertes
tranchées avant tout code (dont une non anticipée par la mission), et clôt
sur le résultat des tests et la vérification bout en bout.

## Partie A — Éléments désignés : forme confirmée, aucun écart

| Élément | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `backend/src/tmis/agents/orchestrator.py` | `Orchestrator.__init__`, sans agent injecté : `AnalysisAgent(document_store=get_document_store())` (kernel `TMISKernel()`, case_store `InMemoryCaseStore()` privés, fabric/governance `None`) ; `VerifierAgent()` (case_store privé) ; `SynthesisAgent()` (kernel et case_store privés, fabric/governance `None`) | Confirmé exact, lignes 115-124 |
| `backend/src/tmis/agents/analysis_agent.py` | `__init__(*, kernel=None, document_store=None, case_store=None, fabric=None, governance=None, firm_id="default")` | Confirmé exact, lignes 67-82 — **non modifié** |
| `backend/src/tmis/agents/synthesis_agent.py` | `__init__(*, kernel=None, case_store=None, summary_generator=None, writing_style_engine=None, fabric=None, governance=None, firm_id="default")` | Confirmé exact, lignes 53-74 — **non modifié** |
| `backend/src/tmis/agents/verifier_agent.py` | `__init__(*, case_store=None, conflict_detector=None, hallucination_engine=None, bias_engine=None)` — ni `kernel` ni `fabric` ni `governance`, l'agent ne fait jamais d'appel génératif | Confirmé exact, lignes 64-77 — **non modifié** |
| `backend/src/tmis/agents/bootstrap.py` | `get_contract_agent()`/`get_jurisprudence_agent()` alimentent déjà `get_kernel()`, `get_case_intelligence_workflow().case_store`, `get_ai_intelligence_fabric()`, `get_ai_governance_platform()`, chacun un singleton `@lru_cache` | Confirmé exact, patron repris à l'identique par `get_orchestrator()` |

Aucun de ces cinq fichiers n'avait un contenu différent de celui attendu
par la mission — aucun arrêt nécessaire, le code a pu commencer
directement (Phase 1, Partie A).

## Partie B — Éléments désignés : forme confirmée, un fait supplémentaire non anticipé

| Élément | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `backend/src/tmis/api/v1/case_intelligence/routes.py` | `_get_profile_or_404(case_id: str, workflow)`, réutilisé par les cinq routes existantes ; `GET /{case_id}/summary` (Sprint 19) déjà un calcul réel, potentiellement génératif, sur `GET`, avec ce même 404 préalable | Confirmé exact, lignes 23-27 et 118-130 |
| `backend/src/tmis/agents/contracts.py` (`AgentInput`) | `task_id: uuid.UUID`, `case_id: uuid.UUID \| None`, `context: dict[str, object]` — un seul `Orchestrator.run(agent_input)` alimente `AnalysisAgent` via `context["document_id"]` et `SynthesisAgent` via `case_id` | Confirmé exact, `tmis/ai/schemas/agent.py:15-21` (`contracts.py` ne fait que ré-exporter) |

**Fait supplémentaire, non anticipé par la mission** : `case_id` sur ce
routeur est une chaîne libre (`CaseStorePort.get(case_id: str)` —
`case_intelligence/cases/ports.py:9`, `in_memory_store.py`) ; les tests
existants du module créent des dossiers avec des identifiants comme
`"case-1"` (`test_case_api.py`), jamais garantis au format UUID. Ce n'est
pas un écart de forme sur un fichier désigné (chacun correspond exactement
à ce qui était annoncé) mais une tension entre deux conventions actées par
des sprints différents : `case_intelligence` (Sprint 19, `case_id`
opaque) et `AgentInput` (Sprint 2, `case_id: uuid.UUID | None`, un
contrat déjà consommé par `chat/routes.py`/`document/routes.py`/
`watch/routes.py` où `case_id` est toujours un paramètre optionnel
accessoire, jamais la ressource première de l'URL). Voir la décision
ci-dessous et docs/168-architecture-exposition-orchestrator.md pour le
détail complet.

## Question Ouverte n°1 (Partie B) — `document_id` en paramètre de requête, ou endpoint séparé ?

**Décision : (a) — paramètre de requête scalaire optionnel,
`?document_id=...`**, confirmant la recommandation par défaut de la
mission. Voir docs/168-architecture-exposition-orchestrator.md pour le
raisonnement complet ; en résumé, `document_id` affine un calcul déjà
déclenché par `case_id` (la ressource racine de l'URL), exactement le rôle
de `domain`/`compare_document_id`/`case_id` sur `GET /documents/
{document_id}/analysis` (Sprint 39) — son absence est un cas géré
normalement par le graphe, pas une erreur.

## Question Ouverte n°2 (Partie B, découverte en Phase 0) — `case_id: str` libre contre `AgentInput.case_id: uuid.UUID | None`

**Décision : même compromis tolérant déjà établi par
`document/routes.py._parse_case_id`/`chat/routes.py._agent_input`** :
`uuid.UUID(case_id)` si possible, `None` sinon. Voir
docs/168-architecture-exposition-orchestrator.md pour le raisonnement
complet et la conséquence documentée (une synthèse vide, avec warning
explicite, pour un `case_id` non-UUID — le même comportement dégradé et
gracieux qu'`AnalysisAgent` applique déjà à un `document_id` manquant).

## Confirmation explicite : aucune signature de contrat modifiée

- `AgentInput`/`AgentOutput`/`AgentPort` (`tmis.ai.schemas.agent`) :
  **aucune ligne modifiée**.
- `AnalysisAgent`, `VerifierAgent`, `SynthesisAgent`
  (`agents/{analysis,verifier,synthesis}_agent.py`) : **aucune ligne
  modifiée** — consommés tels quels par `get_orchestrator()`.
- `Orchestrator` (`agents/orchestrator.py`) : **aucune ligne modifiée** —
  son constructeur acceptait déjà `analysis_agent`/`verifier_agent`/
  `synthesis_agent` en paramètres optionnels (patron établi au Sprint 29).
- `TMISKernel`, `AIIntelligenceFabric`, `AIGovernancePlatform`,
  `CaseStorePort`/`CaseIntelligenceWorkflow` : **aucune ligne modifiée**.
- `ResearchAgent`, `JurisprudenceAgent`, `ContractAgent`, `WatchAgent`,
  leurs accesseurs respectifs dans `agents/bootstrap.py` : **non
  touchés**, hors périmètre de ce sprint.
- `case_intelligence/routes.py` : cinq routes existantes (`profile` x3,
  `timeline`, `summary`, `search`) — **aucune ligne modifiée**, seule une
  sixième route est ajoutée en fin de fichier ; `document/routes.py`,
  `chat/routes.py`, `watch/routes.py` : **non touchés**.
- Comportement d'`Orchestrator()` construit sans arguments (utilisé par
  `tests/unit/test_orchestrator.py`) : **inchangé**, confirmé par un test
  dédié (`test_orchestrator_without_arguments_keeps_its_own_unshared_
  defaults`) et par la suite pytest complète.

## Résultat des tests

- Backend : `pytest -q` (depuis `backend/`) — **2220 passed, 7 skipped**
  (2198 mesurés directement avant ce sprint + 22 nouveaux : 13 dans
  `tests/unit/agents/test_agents_bootstrap.py`, 9 dans
  `tests/integration/case_intelligence/test_case_analysis_api.py`),
  aucune régression.
- `ruff check src/tmis/agents/bootstrap.py src/tmis/api/v1/
  case_intelligence/ tests/unit/agents/test_agents_bootstrap.py
  tests/integration/case_intelligence/test_case_analysis_api.py` → All
  checks passed.
- `mypy src/tmis/agents/bootstrap.py src/tmis/api/v1/case_intelligence/`
  (le dépôt est en `mypy --strict`) → Success, aucune erreur. Une
  vérification `mypy src/tmis` complète confirme que les deux seules
  erreurs restantes dans le dépôt (`sentence_transformers` introuvable
  dans cet environnement d'exécution, `ai/embeddings/adapters/
  sentence_transformer_provider.py` et `ai/reranking/adapters/
  cross_encoder_reranker.py`) préexistent à ce sprint et sont hors de son
  périmètre.

## Vérification bout en bout

**Partie A** (`tests/unit/agents/test_agents_bootstrap.py`, 13 tests) —
comparaisons d'identité (`is`), jamais d'égalité de valeur :

- `get_orchestrator()` est un singleton process-wide.
- Ses trois agents partagent `kernel` avec `get_kernel()` (Analysis,
  Synthesis), `case_store` avec `get_case_intelligence_workflow().
  case_store` (Analysis, Verifier, Synthesis), `fabric` avec
  `get_ai_intelligence_fabric()` (Analysis, Synthesis), `governance` avec
  `get_ai_governance_platform()` (Analysis, Synthesis).
- `AnalysisAgent` partage en plus `document_store` avec
  `get_document_store()`.
- `Orchestrator()` sans arguments garde ses propres agents non partagés
  (`is not` face à ceux de `get_orchestrator()`) et ses défauts
  `fabric`/`governance` à `None`.

**Partie B** (`tests/integration/case_intelligence/
test_case_analysis_api.py`, 9 tests, via `TestClient` — même objet ASGI,
même routage, même injection de dépendances et même persistance sqlite
réelle qu'un `uvicorn` séparé ; aucune instance Postgres n'est disponible
dans cet environnement pour reproduire la vérification manuelle contre un
second processus faite aux Sprints 39/40) :

- Dossier inconnu → `404`.
- Dossier existant, sans `document_id` → `200`, `result["synthesis"]`
  présent, avertissement explicite mentionnant `document_id`.
- Dossier existant, avec un `document_id` réellement traité (upload +
  `process_document_task` exécuté en direct, comme
  `test_document_analysis_api.py`) → entités/`narrative`/`model` peuplés,
  citation sur le document.
- `document_id` inconnu → `200`, résultat d'analyse vide, avertissement
  explicite mentionnant l'identifiant.
- `case_id` au format UUID, dossier créé via `CaseStorePort.get_or_
  create()` → `result["synthesis"]["executive_summary"]` réellement
  peuplé, citation `connector == "case_store"` présente.
- `case_id` non-UUID (`"case-1"`) → `result["synthesis"]["executive_
  summary"] == ""`, avertissement explicite « No case_id provided ».
- Non-régression : `POST /{case_id}/profile` et `GET /{case_id}/summary`
  renvoient exactement le comportement attendu avant ce sprint ; la
  nouvelle route apparaît dans `/openapi.json`.

## Conclusion

Cinq des sept éléments désignés par la mission (les trois constructeurs
d'agents, `orchestrator.py`, `bootstrap.py`) n'avaient aucun écart avec ce
qu'elle annonçait pour la Partie A. Les deux éléments de la Partie B
(`case_intelligence/routes.py`, `contracts.py`) correspondaient également
exactement à ce qui était annoncé, avec un fait comportemental
supplémentaire découvert en Phase 0 — la tension `case_id: str` /
`AgentInput.case_id: uuid.UUID | None` — documenté et tranché avant tout
code, sur le même modèle que la découverte du Sprint 39 sur
`ProcessingStatus`. Les deux questions ouvertes de la Partie B ont été
tranchées en Phase 0 et documentées dans
docs/168-architecture-exposition-orchestrator.md et le rapport
d'architecture. Suite pytest complète verte, `ruff`/`mypy --strict` verts
sur tout le périmètre modifié, aucune régression sur les routes ou tests
existants.
