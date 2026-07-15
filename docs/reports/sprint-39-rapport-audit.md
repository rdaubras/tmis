# Rapport d'audit — Sprint 39 (Exposition de `ContractAgent` dans l'API document)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« PHASE 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), l'état
réel des sept fichiers désignés par la mission, confirme qu'aucun n'a
changé de forme depuis son sprint d'origine, documente une découverte de
comportement faite pendant la Phase 0 elle-même, et clôt sur une
vérification manuelle bout en bout menée contre un vrai serveur
`uvicorn` et une vraie base PostgreSQL.

## Fichiers désignés par le prompt : forme confirmée, aucun écart

| Fichier | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `backend/src/tmis/api/v1/document/routes.py` | `router = APIRouter(prefix="/documents", ...)`, `get_document_store()` partagé (Sprint 37), 404 via `HTTPException` sur `GET /{document_id}` et `GET /{document_id}/versions` | Confirmé exact — patron repris à l'identique pour la nouvelle route |
| `backend/src/tmis/api/v1/document/schemas.py` | `DocumentUploadResponse`, `DocumentVersionResponse`, `DocumentSummaryResponse`, des `BaseModel` Pydantic simples | Confirmé exact |
| `backend/src/tmis/agents/contract_agent.py` | `ContractAgent.run()` lit `context["document_id"]` (obligatoire), `context["domain"]`/`context["compare_document_id"]` (optionnels), `AgentInput.case_id` optionnel ; `result = {clauses, version_diff, synthesis, model}`, `citations` au niveau `AgentOutput` (une par document analysé/comparé) | Confirmé exact — **CTO validé en Phase 0**, forme non modifiée par ce sprint |
| `backend/src/tmis/agents/bootstrap.py` | `get_contract_agent()` (`@lru_cache`), déjà câblé sur le `DocumentStorePort` partagé (Sprint 37), `TMISKernel`/`AIIntelligenceFabric`/`AIGovernancePlatform`/`ClauseEngine`/`CaseStorePort` (Sprint 35) | Confirmé exact — **non modifié**, consommé via `Depends()` |
| `backend/src/tmis/document_intelligence/schemas/document.py` | `ProcessingStatus` avec 15 valeurs dont `OCR_DONE` | Confirmé exact dans sa forme — voir découverte de comportement ci-dessous |
| `backend/src/tmis/api/v1/case_intelligence/routes.py` | `GET /{case_id}/summary` : 404 préalable (`_get_profile_or_404`) puis `await workflow.summarize(case_id)`, un calcul réellement génératif sur verbe `GET` | Confirmé exact — patron de référence direct pour `GET /{document_id}/analysis` |
| `backend/src/tmis/cabinet_knowledge/taxonomy/schemas.py` | `LegalDomain(StrEnum)` : `general`, `civil`, `commercial`, `social`, `fiscal`, `data_protection`, `penal` | Confirmé exact — utilisé tel quel comme type du paramètre `domain` |

Aucun de ces fichiers n'avait un contenu différent de celui attendu par
la mission — aucun arrêt nécessaire, le code a pu commencer directement.

## Découverte de Phase 0 : les statuts intermédiaires de `ProcessingStatus` ne sont jamais posés en pratique

La mission posait la Question Ouverte 1 en présupposant que `RECEIVED`,
`VALIDATED`, `SCANNED` étaient des statuts réellement atteignables avant
`OCR_DONE`. Une recherche exhaustive de chaque `ProcessingStatus.XXX`
réellement assigné à un `DocumentRecord` dans `backend/src/tmis/`
(`grep -rn "ProcessingStatus\." backend/src/tmis/ --include="*.py"`,
hors la déclaration de l'énumération elle-même) ne trouve que deux
affectations dans tout le dépôt :

- `ProcessingStatus.RECEIVED` — `api/v1/document/routes.py`, à l'upload.
- `ProcessingStatus.PROCESSED` — `document_intelligence/pipeline/
  document_pipeline.py:271`, à la toute fin du pipeline, sur succès.

Les treize autres valeurs de l'énumération, dont `OCR_DONE` citée par la
mission, ne sont jamais assignées par le code actuel. Lecture de `stage()`/
`stage_async()` (`document_pipeline.py:130-180`) : en cas d'exception dans
une étape, l'erreur est re-levée telle quelle, sans qu'aucun `DocumentRecord`
ne soit sauvegardé avec un statut `FAILED` — le document reste alors à
`RECEIVED`, son dernier état persisté. Ce n'est pas un écart de forme
(l'énumération correspond exactement à ce qui était attendu par la
mission) mais un fait de comportement qui a directement informé la
décision prise sur la Question Ouverte 1 (voir
docs/166-architecture-exposition-agent-contrats.md) : la garde ajoutée à
la nouvelle route compare le statut à `PROCESSED` (le seul état qui, en
pratique, garantit `ocr_text` non vide) plutôt que de construire un ordre
sur des valeurs qui ne surviennent jamais.

## Confirmation explicite : aucune signature de contrat modifiée

- `AgentInput`/`AgentOutput`/`AgentPort` (`tmis.ai.schemas.agent`) :
  **aucune ligne modifiée**.
- `ContractAgent` (`agents/contract_agent.py`) : **aucune ligne
  modifiée** — consommé tel quel via `get_contract_agent()`.
- `get_contract_agent()` (`agents/bootstrap.py`) : **aucune ligne
  modifiée**.
- `ClauseEngine`, `DocumentStorePort`, `AIIntelligenceFabric`,
  `AIGovernancePlatform` : **aucune ligne modifiée**.
- `WatchAgent`, `Orchestrator`, leurs bootstraps, le chat, `ResearchAgent`,
  `JurisprudenceAgent` : **non touchés**, hors périmètre de ce sprint
  (voir mission).
- `POST /upload`, `GET /{document_id}`, `GET /{document_id}/versions`,
  `process_document_task` : **aucune ligne modifiée** — confirmé par
  lecture directe du diff et par trois tests de non-régression dédiés
  (`test_upload_route_is_unaffected`,
  `test_get_document_route_is_unaffected`,
  `test_versions_route_is_unaffected`), tous verts.

## Résultat des tests

- Backend : `pytest -q` — **2204 passed, 7 skipped** (2192 préexistants +
  12 nouveaux dans `tests/integration/document_intelligence/
  test_document_analysis_api.py`), aucune régression.
- `ruff check src/tmis/api/v1/document tests/integration/
  document_intelligence/test_document_analysis_api.py` → All checks
  passed.
- `mypy src/tmis/api/v1/document` (le dépôt est en `mypy --strict`) →
  Success, aucune erreur.

## Vérification manuelle bout en bout

Contrairement au Sprint 38 (où l'environnement de session ne permettait
pas l'hydratation React), cette session disposait d'un PostgreSQL et
d'un Redis démarrables localement (`service postgresql start`,
`service redis-server start`) — la vérification manuelle a donc pu aller
jusqu'à un vrai serveur `uvicorn tmis.main:app`, une vraie base
PostgreSQL (`alembic upgrade head` exécuté avant démarrage) et un
document réellement traité par `DocumentIntelligencePipeline` :

```
$ curl -X POST http://127.0.0.1:8000/api/v1/documents/upload -F "file=@bail-manuel.txt"
{"document_id":"09bb9a46-...","task_id":"...","status":"received"}

$ curl http://127.0.0.1:8000/api/v1/documents/09bb9a46-.../analysis
409 {"detail":"Document '09bb9a46-...' has not completed processing yet
(status='received'): no OCR text is available to analyze."}

$ curl http://127.0.0.1:8000/api/v1/documents/does-not-exist/analysis
404 {"detail":"No document 'does-not-exist'"}

# process_document_task appelé directement (même fonction qu'un worker Celery
# réel exécuterait — pas de .delay(), aucun worker Celery démarré dans cette
# vérification manuelle) :
$ curl http://127.0.0.1:8000/api/v1/documents/09bb9a46-.../analysis
200 {"document_id":"09bb9a46-...","result":{"clauses":[],"version_diff":null,
"synthesis":"[anthropic:claude-sonnet-5] Analyse le contrat suivant : ...",
"model":"claude-legal"},"citations":[{"source_id":"09bb9a46-...",
"connector":"document_store","excerpt":"...","reference":"bail-manuel.txt"}],
"confidence":"low","warnings":["No clause found in the firm's library for
domain 'commercial'."]}

$ curl "http://127.0.0.1:8000/api/v1/documents/09bb9a46-.../analysis?domain=not-a-domain"
422 {"detail":[{"type":"enum","loc":["query","domain"], ...}]}

$ curl "http://127.0.0.1:8000/api/v1/documents/09bb9a46-.../analysis?compare_document_id=does-not-exist"
200 {"result":{"version_diff":null, ...},
"warnings":["No clause found ...", "Document 'does-not-exist' was not found
in the document store."]}

$ curl http://127.0.0.1:8000/api/v1/documents/09bb9a46-.../versions
200 [{"version":1,"status":"received", ...},{"version":2,"status":"processed", ...}]
```

Tous les comportements attendus ont été observés directement contre le
serveur réel : `404` sur document absent, `409` avant traitement complet
(avec le statut réel dans le message), `200` avec une synthèse
véritablement générée par `TMISKernel.complete()` une fois le document
`PROCESSED`, `422` natif de FastAPI/Pydantic sur un `domain` hors
énumération, dégradation gracieuse (avertissement, pas d'erreur) sur un
`compare_document_id` inexistant, et la route `/versions` renvoyant
toujours ses deux versions (`received` puis `processed`) sans aucune
altération. Serveur et worker arrêtés proprement en fin de vérification
(`pkill uvicorn`/`celery`) ; le rôle et la base PostgreSQL créés pour
cette session (`tmis`/`tmis`) sont locaux à ce conteneur éphémère.

**Découverte opérationnelle, sans rapport avec le code livré** : Redis,
démarré pour cette vérification manuelle (le worker Celery en a besoin
comme broker), avait été laissé actif après coup. `pytest -q` exécuté
juste après a alors échoué sur 66 tests sans rapport avec ce sprint
(`test_watch_agent.py`, `test_synthesis_agent.py`,
`test_platform_sdk_agent_connector_sdk.py`...). Cause : `tmis.ai.cache.
factory.make_cache()` sonde Redis une fois par processus
(`_redis_reachable()`) et bascule sur `RedisCache` — partagé entre tous
les appelants — dès qu'il répond, alors que l'environnement de test
habituel n'a pas de Redis et dégrade silencieusement vers
`InMemoryCache` (une instance privée par `TMISKernel()`, jamais
partagée). Redis actif fait donc fuir un état partagé entre des tests qui
supposent chacun un cache isolé. **Correction** : `service redis-server
stop` avant la suite finale — `pytest -q` repasse à 2204 passed, 7
skipped, confirmant que l'échec était un artefact de l'environnement de
vérification manuelle, pas une régression de ce sprint. Signalé ici pour
quiconque republiera ce protocole de vérification manuelle dans une
session future : arrêter Redis (ou lancer `pytest` dans un processus qui
ne l'a jamais vu) avant de relancer la suite complète.

## Conclusion

Aucun des sept fichiers désignés par le prompt n'avait un contenu
différent de celui attendu. Les deux questions ouvertes ont été
tranchées en Phase 0 avant tout code et documentées dans
docs/166-architecture-exposition-agent-contrats.md et le rapport
d'architecture. Une découverte de comportement a été faite en Phase 0
(statuts intermédiaires de `ProcessingStatus` jamais posés en pratique)
et a directement informé la décision sur la Question Ouverte 1, sans
nécessiter d'arrêt ni de signalement d'écart — la forme des fichiers
elle-même correspondait exactement à ce qui était annoncé.
