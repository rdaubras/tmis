# Rapport d'audit — Sprint 43 (Consolidation de dette technique)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« Phase 0 — Audit obligatoire »). Il confirme ou
infirme, par lecture directe du dépôt (jamais par mémoire), les cinq
prémisses du brief, avant tout code, sur le même principe que les
Sprints 26-28 et 37 : quatre confirmées, une infirmée et tranchée avec
l'utilisateur avant d'écrire la moindre ligne.

## 0. Écart de prémisse trouvé et tranché avec l'utilisateur : `COPILOT_MANAGE`

Le brief affirme : « un bug de permission RBAC similaire (`COPILOT_MANAGE`
accordé à aucun rôle au Sprint 24) a été corrigé au Sprint 25 par un autre
audit manuel, pas par un test ».

**Ceci ne correspond pas à l'historique réel du dépôt.** `git log --all
-S"COPILOT_MANAGE" -- backend/src` ne renvoie qu'un seul commit touchant
cette permission :

```
1813e27 Sprint 24 : Legal Copilot Framework (LCF)
```

`git show 1813e27` montre que `Permission.COPILOT_MANAGE` et son
attribution à `Role.PARTNER`/`Role.IT_ADMIN` dans
`DEFAULT_ROLE_PERMISSIONS` ont été ajoutés **dans le même commit** — la
permission n'a jamais existé sans être accordée. Le rapport
`docs/reports/sprint-24-rapport-architecture.md:131-134` et
`docs/reports/sprint-24-demo-legal-copilot-framework.md:161-163`
documentent explicitement l'origine réelle du bug :

> « `identity_platform/rbac/schemas.py` n'accordait `COPILOT_MANAGE` à
> aucun rôle — chaque endpoint mutateur aurait toujours répondu 403.
> **Découvert en écrivant les tests d'intégration API, corrigé avant de
> committer.** »

Le bug a donc été trouvé et corrigé **à l'intérieur du Sprint 24
lui-même, avant son commit** — jamais livré cassé, et le Sprint 25 n'a
jamais touché `COPILOT_MANAGE` (ses deux seuls commits pertinents,
`4a1fac3` et `4a748f7`, portent sur `KNOWLEDGE_GRAPH_MANAGE`, une
permission différente).

**Décision arbitrée avec l'utilisateur (avant tout code) :** corriger la
narration dans ce rapport plutôt que la reproduire telle quelle, et
conserver malgré tout un test de contrat de régression sur
`COPILOT_MANAGE` — un droit RBAC silencieusement retiré est exactement le
type de rupture de contrat inter-contexte (`identity_platform` ↔
`legal_copilot_framework`) que `tests/contracts/` doit prévenir, quel que
soit le sprint auquel rattacher le quasi-incident historique. Voir
`tests/contracts/test_copilot_manage_permission_contract.py`.

## 1. Types traversant une frontière de bounded context

### 1.1 `AgentInput` / `AgentOutput` (`tmis.ai.schemas.agent`)

Une seule définition de chaque (`ai/schemas/agent.py:15-35`) ;
`agents/contracts.py` n'est qu'un ré-export de compatibilité, pas une
seconde définition.

Six points de construction réels d'`AgentInput`, tous conformes au
contrat `case_id: str | None` (Sprint 42) :

| Point de construction | Fichier:ligne |
|---|---|
| `BaseAgentPlugin.invoke()` | `platform_sdk/agent_sdk/base.py:36-43` |
| `Coordinator.run_mission()` (`case_id` toujours `None`) | `ai_team/coordinator/engine.py:134-136` |
| `GET /cases/{case_id}/analysis` | `api/v1/case_intelligence/routes.py:201-206` |
| Chat `mode="research"`/`"jurisprudence"` (`_agent_input`) | `api/v1/chat/routes.py:42-44` |
| `GET /documents/{document_id}/analysis` | `api/v1/document/routes.py:172` |
| `POST /watches` | `api/v1/watch/routes.py:62-67` |

Le consommateur que le brief signale comme non exercé avant sa
correction, `BaseAgentPlugin.invoke()`, est confirmé : avant Sprint 42,
`case_id=uuid.UUID(str(payload["case_id"]))` levait une `ValueError` non
rattrapée pour tout `case_id` non-UUID (`CaseStorePort` accepte des ids
libres) — un crash silencieux de `invoke()` pour tout plugin tiers
(`AgentFiscalPlugin`, `AgentDroitSocialPlugin`, ...). Le commit de
correction (`ae1cee1`) avait déjà ajouté une régression bout-en-bout
réelle (`test_agent_plugin_invoke_no_longer_raises_on_a_non_uuid_case_id`,
`tests/unit/platform_sdk/test_platform_sdk_agent_connector_sdk.py:52-62`,
et `test_analysis_with_a_non_uuid_case_id_now_populates_the_synthesis`,
`tests/integration/case_intelligence/test_case_analysis_api.py:161-186`)
— la discipline de test du Sprint 42 était donc meilleure que ne le
suggère l'histoire du bug ; l'écart se situait dans le câblage du Sprint
41 lui-même (`case_id` d'abord threadé en `uuid.UUID`), jamais couvert par
un test bout-en-bout avec un id réaliste non-UUID à l'époque.

Ce qui manquait malgré tout : une suite dédiée, indépendante des tests
unitaires par module, drivant `AgentInput` depuis le point de production
le plus en amont (le payload JSON brut du endpoint chat) à travers
*chaque* agent (`AnalysisAgent`, `SynthesisAgent`, `ContractAgent`,
`JurisprudenceAgent`, `WatchAgent`, `ResearchAgent`) **et**
`BaseAgentPlugin.invoke()` dans un seul test paramétré. C'est l'objet de
`tests/contracts/test_agent_input_contract.py`.

### 1.2 `Citation` (`tmis.ai.schemas.citation`)

Une seule classe `Citation` dans tout le dépôt (`ai/schemas/citation.py:
4-12`). Deux schémas apparentés existent, jamais fusionnés avec elle :

- `ResearchCitation` (`legal_research/citations/schemas.py:4-16`, 6
  champs — `source_id, title, date, document_type, reference, excerpt`) ;
- `DraftCitation` (`legal_drafting/citations/schemas.py:4-21`), qui
  « étend conceptuellement » `ResearchCitation` sans jamais la réutiliser.

L'adaptateur explicite `research_citation_to_citation`
(`agents/citations.py:6-23`) convertit `ResearchCitation` → `Citation`,
en tirant `connector` d'un `ResearchResult` apparié plutôt que de
`ResearchCitation` elle-même. Trois appelants
(`research_agent.py:73`, `watch_agent.py:104`, `jurisprudence_agent.py:
93`) font :

```python
zip(response.results, research_citations, strict=True)
```

`strict=True` garantit une longueur égale, **pas un appariement correct**
— un risque latent identique en nature au bug `case_id` (« ça a l'air
bon, c'est silencieusement faux »). Aucun test existant ne pilotait ce
chemin depuis un vrai `ResearchOrchestrator.search()` jusqu'aux `Citation`
adaptées — seulement des fixtures construites à la main de part et
d'autre de l'adaptateur. Couvert désormais par
`tests/contracts/test_citation_contract.py`, contre le vrai singleton
`get_research_orchestrator()` et les connecteurs fixtures du Sprint 2
(aucun identifiant PISTE n'est configuré dans cet environnement, voir
§3).

### 1.3 `KnowledgeRelation` (`tmis.cabinet_knowledge.ontology.schemas`)

Une seule définition (`cabinet_knowledge/ontology/schemas.py:30-42`),
délibérément partagée par deux producteurs dans deux bounded contexts
différents : `OntologyEngine.link()` (`cabinet_knowledge/ontology/
engine.py:33-41`, relations entre `KnowledgeObject`s) et
`GraphEngine.link()` (`legal_knowledge_graph/graph_core/engine.py:
69-79`, relations entre `GraphNode`s, avec les champs `explanation`/
`confidence` ajoutés au Sprint 25). Le commit `4a748f7` (Sprint 25,
« suppression du doublon knowledge_graph ») confirme qu'un module
réellement dupliqué a bien été supprimé à l'époque — les deux engines
actuels sont les survivants intentionnellement séparés, pas un reliquat.
Chacun est déjà testé contre son propre moteur réel
(`tests/unit/legal_knowledge_graph/test_graph_core.py:37-58` notamment),
mais aucun test ne confirmait qu'une `KnowledgeRelation` produite par
l'un des deux producteurs reste consommable par le store de l'autre —
la preuve qu'il s'agit d'un seul contrat, pas de deux formes
coïncidentes. Ajouté dans
`tests/contracts/test_knowledge_relation_contract.py`.

### 1.4 `ResearchCitation` (`tmis.legal_research.citations.schemas`)

Un seul producteur (`CitationEngine.build()`,
`legal_research/citations/engine.py:11-19`), consommé par les
formatters, `ResearchOrchestrator.get_citations()`, et par l'adaptateur
`agents/citations.py` (§1.2). Champ testé structurellement (pas
seulement en unitaire isolé) dans
`tests/contracts/test_citation_contract.py::
test_research_citation_shape_matches_what_the_adapter_expects`.

## 2. `case_intelligence` : `InMemoryCaseStore` confirmé comme défaut, câblage recensé

Confirmé par lecture directe : `case_intelligence.bootstrap.
get_case_intelligence_workflow()` (avant ce sprint) ne passait **aucun**
`case_store` à `CaseIntelligenceWorkflow(...)`, ce qui déclenchait le
défaut du workflow lui-même
(`case_intelligence/workflow/case_workflow.py:86`,
`self.case_store: CaseStorePort = case_store or InMemoryCaseStore()`).
Tous les endpoints synchrones `/api/v1/cases/*`
(`api/v1/case_intelligence/routes.py`, 6 routes, toutes dépendantes de
`Depends(get_case_intelligence_workflow)`) partageaient donc le même
singleton `InMemoryCaseStore` en mémoire de processus — de même que
`agents.bootstrap.get_orchestrator()`/`get_contract_agent()`/
`get_jurisprudence_agent()`, qui réutilisent délibérément
`get_case_intelligence_workflow().case_store` plutôt que d'introduire un
troisième store (docstrings explicites, `agents/bootstrap.py:42-44,
60-61, 106-118`).

Seul le chemin Celery (`core/tasks/case_tasks.py:31-35`,
`trigger_case_workflow_task`) construisait un `SQLAlchemyCaseStore()` —
une nouvelle instance par tâche, jamais partagée. `CaseStorePort` (le
Protocol, `case_intelligence/cases/ports.py:6-15`) est implémenté à
l'identique par les deux adaptateurs — la divergence est purement une
question de câblage (quelle instance chaque composition root construit),
pas un désaccord d'interface.

Composition roots recensés qui construisent ou capturent un `CaseStorePort` :

| # | Fichier:ligne | Ce qu'il construit |
|---|---|---|
| 1 | `case_intelligence/workflow/case_workflow.py:86` | Défaut `InMemoryCaseStore()` (fallback du constructeur) |
| 2 | `case_intelligence/bootstrap.py` (avant ce sprint) | Ne passait pas de `case_store` → déclenche #1 |
| 3 | `core/tasks/case_tasks.py:32` (avant ce sprint) | `SQLAlchemyCaseStore()` neuf à chaque appel |
| 4-8 | `agents/{analysis,synthesis,contract,jurisprudence}_agent.py` | Défauts `InMemoryCaseStore()` propres à chaque agent, ne se déclenchent que si l'agent est construit hors `agents.bootstrap` (jamais le cas en production, voir ci-dessus) |
| 9 | `backend/scripts/seed_beta_pilot.py:88` | `InMemoryCaseStore()` — script de démo pilote, explicitement éphémère (docstring), hors composition roots applicatifs |

Aucune preuve de données de production dans `InMemoryCaseStore` : aucun
script de migration ne déplace de données hors de la mémoire, et
`seed_beta_pilot.py` est explicitement documenté comme jetable. Confirmé
conforme à l'hypothèse du brief (« aucune migration n'est dans le
périmètre »).

**Correction apportée ce sprint** (voir
`docs/reports/sprint-43-rapport-architecture.md` pour le détail) : ajout
de `case_intelligence.bootstrap.get_case_store()` (singleton
`@lru_cache`, même patron que `document_intelligence.bootstrap.
get_document_store()` du Sprint 37), injecté dans
`get_case_intelligence_workflow()` et dans
`core.tasks.case_tasks.trigger_case_workflow_task` — les deux seuls
points qui devaient converger. `docs/151-architecture-persistance.md`
mis à jour en conséquence.

## 3. Redis / Qdrant / PISTE : aucune validation réelle possible dans cet environnement

### Redis (`ai.cache.factory.make_cache()`)

Gate par **joignabilité**, pas seulement par présence de variable :
`_shared_redis_client()` (`ai/cache/factory.py:46-73`) exécute un `PING`
synchrone (timeout 0.5s) et retombe sur `InMemoryCache()` sans jamais
lever d'exception si Redis ne répond pas. `TMIS_REDIS_URL` a une valeur
par défaut non vide (`redis://localhost:6379/0`,
`core/config.py:19`) — mais aucun Redis n'écoute sur ce port dans cet
environnement (`docker ps` échoue : aucun démon Docker disponible ;
`redis-cli`/connexion socket directe confirment `Connection refused`).

Tests gatés par `TMIS_REDIS_URL` (`tests/integration/ai/
test_redis_backends.py:5-9`) : **jamais exécutés en CI**
(`.github/workflows/ci.yml` ne définit ni service `redis` ni variable
`TMIS_REDIS_URL` dans l'étape de test — seul `TMIS_DATABASE_URL` l'est) ni
dans cet environnement (variable absente). `docker-compose.yml:18-26`
définit bien un service `redis:7-alpine` pour le développement local,
mais rien de tel n'est actif ici.

### Qdrant (`ai.rag.indexing` / `ai.rag.adapters.qdrant_*`)

Gate par simple drapeau (`TMIS_RAG_VECTOR_INDEX_BACKEND`, défaut
`"memory"`), sans sonde de joignabilité contrairement à Redis. Le seul
test « intégration » existant sur `QdrantVectorIndex`
(`tests/integration/ai/test_qdrant_vector_index_integration.py`) utilise
`AsyncQdrantClient(location=":memory:")` — un moteur Qdrant embarqué en
mémoire de processus, jamais le client réseau (`get_qdrant_client()`/
`TMIS_QDRANT_URL`) que `get_vector_index()` construirait réellement en
production. Le docstring du fichier documente déjà cette limite
(« aucun démon Docker disponible dans cet environnement »).

### PISTE / Légifrance / Judilibre (`ai.connectors.factory`)

Gate par simple présence de `TMIS_PISTE_CLIENT_ID`/
`TMIS_PISTE_CLIENT_SECRET` (`_piste_configured()`,
`ai/connectors/factory.py:16-18`), jamais renseignés dans cet
environnement ni en CI. Tous les tests existants
(`tests/unit/ai/test_connectors_piste_adapters.py`) exercent
`LegifranceConnector`/`JudilibreConnector` contre des fausses réponses
HTTP (`httpx.MockTransport`), jamais contre le service réel. Le proxy
sortant de cet environnement bloque de toute façon les hôtes non
allowlistés — confirmé en pratique par un précédent (Sprint 27, blocage
`403 Forbidden` vers `huggingface.co`, documenté dans
`docs/153-architecture-rag-production.md:132-135`), pas une supposition.

### Conclusion : impossibilité confirmée, pas simulée

Conformément à la consigne du brief (« ne pas simuler artificiellement un
succès »), aucune tentative de connexion réelle n'a été faite contre un
service qui n'existe pas dans cet environnement. Voir le runbook
ci-dessous pour la procédure de validation à exécuter en préproduction.

#### Runbook de validation Redis / Qdrant / PISTE (préproduction, avant tout lancement commercial)

**1. Redis**
```bash
docker compose up -d redis   # ou pointer TMIS_REDIS_URL vers une instance managée
export TMIS_REDIS_URL=redis://<host>:6379/0
cd backend && pytest tests/integration/ai/test_redis_backends.py -v
```
Critère de succès : les 3 tests passent (`test_redis_cache_roundtrip`,
`test_make_cache_selects_redis_when_reachable`,
`test_redis_memory_store_roundtrip`) ; `GET /health` (si un composant
`connector_backends`/cache y est ajouté) ne rapporte plus `degraded` pour
le cache.

**2. Qdrant**
```bash
docker compose up -d qdrant
export TMIS_RAG_VECTOR_INDEX_BACKEND=qdrant
export TMIS_QDRANT_URL=http://<host>:6333
cd backend && python -c "
from tmis.ai.rag.factory import get_vector_index
import asyncio
index = get_vector_index(dimensions=8)
asyncio.run(index.upsert('smoke-test', [0.1]*8, {}))
print(asyncio.run(index.search([0.1]*8, top_k=1)))
"
```
Critère de succès : la commande ci-dessus s'exécute sans exception
réseau et retourne le point inséré. Ajouter un test d'intégration dédié
contre le client réseau (pas `:memory:`) une fois cette validation faite
une première fois manuellement.

**3. PISTE (Légifrance / Judilibre)**
```bash
export TMIS_PISTE_CLIENT_ID=<id fourni par la DILA>
export TMIS_PISTE_CLIENT_SECRET=<secret>
cd backend && python -c "
import asyncio
from tmis.ai.connectors.factory import build_codes_connector, build_jurisprudence_connector
codes = build_codes_connector()
print(asyncio.run(codes.search('contrat de travail', limit=1)))
"
```
Critère de succès : une réponse HTTP 200 réelle de `oauth.piste.gouv.fr`
puis de `legifrance` — pas une `ValueError`/`TimeoutError` réseau. Vérifier
également que le connecteur bascule vers la fixture (`connector.
fixture_fallback` dans les logs) si les identifiants sont retirés, pour
confirmer que le repli reste fonctionnel après validation du chemin réel.

**Point commun aux trois** : dans chaque cas, la bascule fixture ↔ réel se
fait par variable d'environnement seule, sans redéploiement de code —
seule la joignabilité réelle du service manque dans les deux
environnements disponibles à ce jour (ce bac à sable, la CI).

## 4. Marketplace : trois mécanismes confirmés, un écart non documenté trouvé

Voir `docs/171-audit-marketplace.md` pour le recensement complet (trois
tableaux comparatifs + recommandation). Résumé : `platform_sdk.
marketplace` (catalogue/découverte), `business_platform.
marketplace_subscriptions` (facturation, wrapper confirmé autour du
premier — `MarketplaceSubscriptionEngine.subscribe` appelle
`MarketplaceEngine.install` directement), et `legal_copilot_framework`
(`PluginType.COPILOT`, publication uniquement) coexistent bien comme
l'avait diagnostiqué l'audit du Sprint 24
(`docs/144-guide-marketplace-legal-copilot-framework.md`). Ce qui n'était
pas documenté : l'**activation par cabinet** d'un copilote
(`CopilotEngine.activate`, `POST /legal-copilots/{id}/install`) ne passe
par aucun des deux autres mécanismes — ni `ExtensionEngine.install`, ni
`MarketplaceSubscriptionEngine.subscribe`. Un copilote peut donc être
« activé » sans jamais être « installé » ni facturé, et réciproquement.
Documenté comme recommandation pour un sprint futur dédié, aucune fusion
n'est faite dans ce sprint (hors périmètre explicite).

## Résultat des tests (après implémentation)

- Suite complète (`pytest -q`, depuis `backend/`) : **2251 passed, 7
  skipped** (2233 mesurés comme référence avant tout changement de ce
  sprint, +18 nouveaux tests dans `tests/contracts/` — 9 pour
  `AgentInput`/`AgentOutput`, 3 pour `COPILOT_MANAGE`, 3 pour
  `Citation`/`ResearchCitation`, 3 pour `KnowledgeRelation` — aucune
  régression).
- 25 tests d'intégration existants ont dû être adaptés (isolation SQLite
  ajoutée) suite au changement de défaut `case_intelligence` — voir
  `docs/reports/sprint-43-rapport-architecture.md` pour le détail
  fichier par fichier ; aucune assertion métier modifiée, uniquement les
  fixtures de câblage base de données.
- `ruff check src tests` → All checks passed.
- `mypy src` (`--strict`) → Success: no issues found in 1899 source
  files.
- Ordre des tests vérifié non significatif : exécution du sous-ensemble
  `case_intelligence`/`chat`/`legal_drafting`/`legal_reasoning` en ordre
  inverse de fichiers → même résultat (43 passed), confirmant que
  l'isolation SQLite ajoutée ne dépend pas de l'ordre de collecte
  pytest (un risque réel avant correction : un test réutilisait
  silencieusement l'état laissé par un fichier précédent via le bind
  global `SessionLocal`).

## Conclusion

Quatre des cinq prémisses du brief se confirment à la lecture directe du
code. La cinquième (`COPILOT_MANAGE`, Sprint 24→25) ne se confirme pas et
a été tranchée avec l'utilisateur avant tout code (§0) : narration
corrigée, test de régression conservé. Le câblage `case_intelligence` a
convergé sur `SQLAlchemyCaseStore` sans rupture de contrat public ni
migration de données. Redis/Qdrant/PISTE restent non validés contre un
service réel dans les deux environnements disponibles (ce bac à sable,
la CI) — documenté comme une impossibilité confirmée, avec un runbook
actionnable pour la préproduction, jamais simulé. Le triple mécanisme de
marketplace est confirmé et un écart de réconciliation supplémentaire
(activation copilote non liée à l'installation/facturation) est
documenté pour arbitrage futur, sans fusion dans ce sprint.
