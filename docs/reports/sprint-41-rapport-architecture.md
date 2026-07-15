# Rapport d'architecture — Sprint 41 (Consolidation + Exposition d'`Orchestrator`)

## Résumé

Le Sprint 41 clôt la série des quatre sprints d'exposition (Sprints
38-41, voir la note de révision Sprint 38 dans
docs/09-roadmap-30-sprints.md) en deux parties strictement ordonnées.

**Partie A — consolidation** : `agents/bootstrap.py` gagne un nouvel
accesseur, `get_orchestrator()` (`@lru_cache`), qui construit
`AnalysisAgent`/`VerifierAgent`/`SynthesisAgent` avec les quatre
singletons déjà partagés par `get_contract_agent()`/
`get_jurisprudence_agent()`/`get_watch_agent()` — `TMISKernel`,
`CaseStorePort` (`get_case_intelligence_workflow().case_store`),
`AIIntelligenceFabric`, `AIGovernancePlatform` — plutôt que les instances
privées non partagées qu'`Orchestrator()` construit par défaut.
`Orchestrator()` sans arguments garde ce comportement par défaut
inchangé ; `agents/orchestrator.py` et les trois agents du graphe ne sont
pas modifiés.

**Partie B — exposition** : `GET /cases/{case_id}/analysis`, une sixième
route sur l'API `case_intelligence` existante (Sprint 19), câblée sur
`get_orchestrator()` (Partie A). `document_id` est un paramètre de requête
scalaire optionnel, confirmant la recommandation par défaut de la
mission. Une tension non anticipée entre le `case_id: str` libre de ce
routeur et le contrat partagé `AgentInput.case_id: uuid.UUID | None` a été
découverte en Phase 0 et tranchée par le même compromis de parsing
tolérant déjà en place pour `document`/`chat` (voir ci-dessous).

Périmètre livré : `tmis/agents/bootstrap.py` (nouvel accesseur),
`tmis/api/v1/case_intelligence/routes.py` (nouvelle route `get_analysis`,
helpers `_parse_case_id_for_agent`/`_to_analysis_response`),
`tmis/api/v1/case_intelligence/schemas.py` (`CaseAnalysisResponse` et ses
modèles imbriqués, `CitationResponse`), 13 tests unitaires nouveaux
(`tests/unit/agents/test_agents_bootstrap.py`) + 9 tests d'intégration
nouveaux (`tests/integration/case_intelligence/test_case_analysis_api.py`),
0 test existant modifié, docs/169-architecture-consolidation-
orchestrateur.md, docs/168-architecture-exposition-orchestrator.md, note
de révision dans docs/09-roadmap-30-sprints.md.

**Aucun autre agent touché. `agents/orchestrator.py`,
`agents/analysis_agent.py`, `agents/synthesis_agent.py`,
`agents/verifier_agent.py` non modifiés. Zéro changement de signature sur
`AgentInput`/`AgentOutput`/`AgentPort`/les constructeurs des trois agents.
`Orchestrator()` sans arguments garde son comportement inchangé.
`/watches`, `/documents/*`, `/chat/stream` et les cinq autres routes de
`case_intelligence/routes.py` inchangées.**

## Décisions structurantes

### Partie A : pourquoi un document dédié plutôt qu'une section de plus dans docs/151

docs/151 documente la persistance au sens strict (adaptateurs
`SQLAlchemy*Store`, singleton `DocumentStorePort` partagé au Sprint 37).
Ce sprint consolide quatre singletons sur trois agents à la fois — une
composition de l'ampleur de `get_contract_agent()`/
`get_jurisprudence_agent()`/`get_watch_agent()` (des agents ordinaires du
même `agents/bootstrap.py`), pas un correctif de persistance isolé. Un
document dédié (docs/169), sur le modèle des documents par agent
(docs/162/163/164), est donc plus fidèle à la nature du changement.

### Partie A : pourquoi `VerifierAgent` ne reçoit que `case_store`

Les trois constructeurs n'acceptent pas tous les quatre mêmes paramètres :
`VerifierAgent.__init__` n'a que `case_store`/`conflict_detector`/
`hallucination_engine`/`bias_engine` — ni `kernel` ni `fabric` ni
`governance` (il ne fait jamais d'appel génératif, voir
docs/159-architecture-agent-verificateur.md). `get_orchestrator()` ne lui
passe donc que ce qu'il consomme réellement — passer des paramètres qu'un
constructeur n'accepte pas n'est pas une option, et lui en injecter
d'inutilisés n'aurait aucun sens.

### Partie B — Question ouverte 1 : `document_id` en paramètre de requête, confirmé

**Décision : (a) — `?document_id=...`, confirmant la recommandation par
défaut de la mission — aucune divergence trouvée en Phase 0.**

`document_id` affine un calcul déjà déclenché par `case_id` (la ressource
racine de l'URL), exactement le rôle de `domain`/`compare_document_id`/
`case_id` sur `GET /documents/{document_id}/analysis` (Sprint 39). Un
endpoint séparé aurait forcé `document_id` à exister pour que la route
réponde, alors que son absence est un cas géré normalement par le graphe
(`AnalysisAgent` rapporte un `AgentOutput` vide plus un warning,
`SynthesisAgent` tourne quand même) — le même raisonnement qui avait déjà
écarté une ressource imbriquée forcée pour `WatchAgent` au Sprint 40.

### Partie B — Question ouverte 2 (découverte en Phase 0) : `case_id: str` libre contre `AgentInput.case_id: uuid.UUID | None`

Cette tension n'était pas anticipée par la mission. `case_intelligence`
(Sprint 19) traite `case_id` comme un identifiant opaque quelconque (les
tests existants du module créent des dossiers `"case-1"`, jamais garantis
UUID) ; `AgentInput` (Sprint 2) le type en UUID parce que ses autres
appelants (`chat`, `document`, `watch`) le traitent comme un paramètre
optionnel accessoire, jamais comme la ressource première de l'URL.

**Décision : suivre le même compromis tolérant déjà établi par
`document/routes.py._parse_case_id`/`chat/routes.py._agent_input`** :
`uuid.UUID(case_id)` si possible, `None` sinon, sans jamais faire échouer
la requête — plutôt qu'élargir le type d'`AgentInput.case_id`, un contrat
partagé par les sept agents de ce dépôt et leurs quatre points d'exposition
existants, que la mission confirme explicitement en Phase 0 sans demander
de le changer.

**Conséquence assumée** : pour un `case_id` non-UUID (le cas le plus
courant dans les tests existants), le `404` préalable confirme que le
dossier existe, mais `SynthesisAgent` ne reçoit ensuite aucun `case_id`
exploitable et rapporte « No case_id provided... » avec un
`result["synthesis"]` vide — le même comportement dégradé, gracieux et
déjà documenté qu'`AnalysisAgent` applique à un `document_id` manquant,
pas un bug introduit par ce sprint. `analysis`/`verifier`/`verifier_final`
tournent normalement dans tous les cas. Voir
docs/168-architecture-exposition-orchestrator.md pour le détail complet et
les deux tests dédiés qui observent chacun des deux chemins.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `get_orchestrator()` | `get_kernel()`, `get_case_intelligence_workflow().case_store`, `get_ai_intelligence_fabric()`, `get_ai_governance_platform()`, `get_document_store()` (tous Sprint 2-37) | Un second `TMISKernel`/`InMemoryCaseStore` privé, un second `Orchestrator` par appel |
| `get_analysis()` | `get_orchestrator()` (Partie A, via `Depends()`), `_get_profile_or_404` (déjà utilisé par les cinq autres routes) | Un second contrôle d'existence, un second câblage d'agents |
| `_parse_case_id_for_agent()` | Même compromis tolérant que `document/routes.py`/`chat/routes.py` | Une seconde convention de parsing `case_id` |
| `_to_analysis_response()` | `CaseAnalysisResultResponse.model_validate()` (Pydantic) | Un mapping champ par champ dupliquant la forme d'`AgentOutput.result` |
| `CaseAnalysisResponse` | Forme d'`AgentOutput` (même patron que `ContractAnalysisResponse`/`WatchResponse`) | Une forme de réponse aplatie ou renommée sans raison |

## Vérification finale

- `ruff check src/tmis/agents/bootstrap.py src/tmis/api/v1/case_intelligence/
  tests/unit/agents/test_agents_bootstrap.py
  tests/integration/case_intelligence/test_case_analysis_api.py` → All
  checks passed.
- `mypy` (`mypy --strict`) sur les mêmes fichiers → Success, aucune erreur
  (les deux seules erreurs `mypy` restantes dans le dépôt,
  `sentence_transformers` introuvable dans cet environnement, préexistent
  à ce sprint et sont hors de son périmètre).
- `pytest -q` (suite complète) → **2220 passed, 7 skipped** (2198
  préexistants, mesurés directement avant ce sprint, + 22 nouveaux : 13
  dans `test_agents_bootstrap.py`, 9 dans `test_case_analysis_api.py`),
  aucune régression.
- Vérification manuelle bout en bout : via le `TestClient` FastAPI (même
  objet ASGI, même routage, même injection de dépendances, même
  persistance sqlite réelle qu'un `uvicorn` séparé) plutôt qu'un second
  processus `uvicorn` — cet environnement ne dispose d'aucune instance
  Postgres, nécessaire au `DocumentStorePort` partagé désormais utilisé
  par `Orchestrator` (Partie A). Détail complet dans
  docs/reports/sprint-41-rapport-audit.md.

## Frontend : décision de rester backend-only

Même décision et même raisonnement qu'aux Sprints 39/40 (docs/166/167) :
aucun écran affichant un `case_id` réel n'existe aujourd'hui côté
frontend. Ce travail reste pour un sprint frontend dédié.

## Confirmation explicite : la série de quatre sprints d'exposition est complète

Avec ce sprint, les sept agents de ce dépôt (`ResearchAgent`,
`JurisprudenceAgent`, `ContractAgent`, `WatchAgent` — Sprints 33-36 —
plus `AnalysisAgent`/`VerifierAgent`/`SynthesisAgent` du graphe
`Orchestrator` — Sprints 29-31) sont désormais tous réels et tous
atteignables par une route HTTP. La table détaillée des 41 sprints et son
total restent inchangés — voir la note de révision correspondante dans
docs/09-roadmap-30-sprints.md.
