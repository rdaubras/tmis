# Rapport d'architecture — Sprint 40 (Exposition de `WatchAgent`)

## Résumé

Le Sprint 40 ajoute un nouveau routeur, `POST /watches`, câblé sur
`WatchAgent` — réel depuis le Sprint 36, non modifié par ce sprint. La
Phase 0 de re-audit (docs/reports/sprint-40-rapport-audit.md) a confirmé
que les six éléments désignés avaient le contenu attendu et a tranché les
deux décisions de conception explicitement laissées ouvertes par la
mission avant tout code.

Périmètre livré : `tmis/api/v1/watch/routes.py` (nouvelle route
`run_watch`, helpers `_parse_case_id`/`_to_watch_response`),
`tmis/api/v1/watch/schemas.py` (`WatchRequest`, `WatchResponse` et ses
modèles imbriqués), l'enregistrement du nouveau routeur dans
`tmis/api/v1/router.py`, 6 tests d'intégration nouveaux, 0 test existant
modifié, docs/167-architecture-exposition-agent-veille.md, note de
révision dans docs/09-roadmap-30-sprints.md.

**Aucun autre agent touché. `WatchAgent`, `get_watch_agent()` non
modifiés. Zéro changement de signature sur `AgentInput`/`AgentOutput`/
`AgentPort`/`WatchAgent.run()`. `case_intelligence`, `document`, `chat`
inchangés. Aucune persistance de `known_result_ids` introduite — la
décision du Sprint 36 (agent sans état) n'est pas rouverte.**

## Décisions structurantes

### Question ouverte 1 : routeur autonome `POST /watches`, pas `/cases/{case_id}/watch`

La mission posait explicitement cette question comme non dérivable du
code seul : contrairement à `ContractAgent` (rattaché sans ambiguïté à un
document, Sprint 39) et `ResearchAgent`/`JurisprudenceAgent` (rattachés au
chat par leur forme "une requête → un résultat", Sprints 33/38),
`WatchAgent` n'a pas d'ancrage évident, son `case_id` étant optionnel dans
l'agent.

**Décision : (a) — `POST /watches`, `case_id` optionnel dans le corps de
la requête.**

Le critère décisif trouvé en Phase 0 : les deux ressources imbriquées
existantes du dépôt (`/cases/{case_id}/...`, `/documents/{document_id}
/...`) partagent une même propriété — le segment de chemin identifie une
ressource **qui doit déjà exister**, vérifiée par un 404 préalable
(`_get_profile_or_404`, `get_document_store().get(document_id)`).
`WatchAgent.run()` ne fait aucune vérification de ce type sur `case_id` :
il le transmet tel quel à `ResearchOrchestrator.search(case_id=...)` pour
le seul historique, sans jamais appeler un `CaseStorePort`. Router
`/cases/{case_id}/watch` créerait donc, côté API, une attente (un dossier
déjà créé) que l'agent lui-même n'exige jamais — précisément le type de
contrainte que la mission demandait d'éviter « sauf raison produit
explicite et documentée », et qu'aucune autre route de ce dépôt n'impose à
un agent dont le `case_id` est déjà optionnel ailleurs :
`ResearchAgent`/`JurisprudenceAgent`, dont le `case_id` en mode chat est
tout aussi optionnel (`ChatMessageRequest.case_id: str | None = None`),
n'ont jamais été rattachés à un dossier dans leur URL non plus — c'est un
champ du payload, jamais un segment de chemin. `WatchAgent` suit
exactement le même principe.

Le contre-argument produit (« surveiller ce sujet pour ce dossier » est
l'usage probable) reste valable mais concerne un sprint futur de
planification de veilles nommées et persistées, pas celui-ci : ce sprint
expose exactement ce que `WatchAgent.run()` fait aujourd'hui — une
exécution ponctuelle à la demande — pas une configuration de veille
durablement attachée à un dossier.

### Question ouverte 2 : `POST` avec corps de requête, pas `GET` avec paramètres liste

**Décision : `POST`, confirmée — pas de divergence trouvée en Phase 0.**

Recherche exhaustive (`grep -n "@router\.\(get\|post\|patch\|delete\)"`
sur tous les `routes.py` du dépôt) : confirmé qu'aucun `GET` existant
n'accepte de paramètre de requête en forme de liste — les seuls
paramètres `GET` observés sont scalaires (`q`, `domain`,
`compare_document_id`, `case_id`). `connectors` et `known_result_ids` sont
tous deux des listes (`list[str] | None`). FastAPI sait exposer des listes
en paramètres `GET` (répétition `?connectors=a&connectors=b`), mais
introduire ce mécanisme pour ce seul sprint créerait le premier précédent
de ce genre dans ce dépôt, alors qu'un corps de requête `POST`
(`WatchRequest`) est déjà la convention systématique retenue ailleurs pour
transporter une structure à plusieurs champs (`ChatMessageRequest`,
`CaseProfileCreateRequest`). `POST` est donc le choix le plus cohérent
avec le reste du dépôt, sans introduire de convention nouvelle pour un cas
unique.

### `query` obligatoire dans `WatchRequest`, validé par Pydantic — pas seulement par l'agent

`WatchAgent.run()` accepte déjà un `query` manquant en silence (retombe
sur un `AgentOutput` dégradé, confiance `LOW`, aucune recherche lancée) —
un comportement adapté à un appelant interne dont le contexte peut
légitimement ne pas comporter de `query` (un futur `Orchestrator`, par
exemple). Une route publique n'a pas la même contrainte :
`WatchRequest.query: str` est un champ obligatoire du corps de requête,
exactement comme `ChatMessageRequest.message: str` l'est déjà pour le
chat — une requête sans `query` reçoit donc un `422` natif de
FastAPI/Pydantic avant même d'atteindre `WatchAgent`, même principe de
validation à la frontière que `domain: LegalDomain | None` au Sprint 39
(docs/166).

### `connectors`/`known_result_ids` ajoutés au contexte seulement s'ils sont fournis

```python
context: dict[str, object] = {"query": payload.query}
if payload.connectors is not None:
    context["connectors"] = payload.connectors
if payload.known_result_ids is not None:
    context["known_result_ids"] = payload.known_result_ids
```

`WatchAgent._resolve_connectors`/`_resolve_known_ids` distinguent déjà
« absent du contexte » (`None`, tous connecteurs enregistrés interrogés) de
« liste vide fournie » (un choix explicite de l'appelant qui ne matchera
aucun connecteur). Toujours poser la clé dans `context`, même avec une
liste vide par défaut Pydantic, aurait confondu ces deux cas — la route
ne pose donc la clé que lorsque le client l'a réellement fournie.

### `case_id` : même compromis tolérant que `document`/`chat`, aucune validation d'existence

`_parse_case_id()` reprend, pour la conversion `str -> uuid.UUID | None`,
exactement le même compromis tolérant que `tmis.api.v1.document.
routes._parse_case_id`/`tmis.api.v1.chat.routes._agent_input` : un
identifiant qui ne parse pas comme UUID devient `None` plutôt que de faire
échouer la requête. Aucune vérification d'existence n'est ajoutée
au-dessus — `WatchAgent` n'en fait lui-même aucune, contrairement à
`ContractAgent`/`JurisprudenceAgent` qui résolvent un vrai `CaseProfile`.

### Mapping de réponse : `model_validate`, même patron que Sprint 39

```python
class WatchResponse(BaseModel):
    result: WatchResultResponse
    citations: list[CitationResponse]
    confidence: str
    warnings: list[str]
```

`WatchResultResponse.model_validate(output.result)` retrouve les sept clés
confirmées en Phase 0 (`search_id`, `query`, `connectors_used`,
`result_ids`, `new_results`, `alert_message`, `model`), y compris la liste
imbriquée `new_results`, sans redéclarer aucun nom de champ dans la route
— même usage que `_to_analysis_response()` au Sprint 39, pour la même
raison (`output.result: dict[str, object]`, `mypy --strict` exige un
narrowing que `model_validate` fournit nativement).

## Bug corrigé en cours d'implémentation, hors du champ initial du diff

Aucun — ce sprint n'a touché aucun code préexistant en dehors de l'ajout
additif décrit ci-dessus (un nouveau module `api/v1/watch/`, une ligne
d'enregistrement dans `api/v1/router.py`).

## Test existant modifié : aucun

Les 2204 tests préexistants (Sprints 1 à 39 inclus) passent tous sans
modification — vérifié par exécution complète (`pytest -q`, 2210 passed,
7 skipped). 6 tests nouveaux dans
`tests/integration/api/test_watch_api.py` :

- `test_watch_with_query_only`
- `test_watch_filtered_to_a_connector`
- `test_watch_excludes_already_known_result_ids`
- `test_watch_with_a_case_id`
- `test_watch_without_a_case_id`
- `test_watch_rejects_a_request_without_a_query`

Aucun test n'utilise `app.dependency_overrides` — `WatchAgent` est
consommé via le singleton `get_watch_agent()` réel, même patron que
`research_agent`/`jurisprudence_agent`/`contract_agent` déjà en place.
Contrairement aux tests `document`/`case_intelligence`, aucune base sqlite
n'est nécessaire ici : `WatchAgent` ne touche ni `CaseStorePort` ni
`DocumentStorePort`, seulement `ResearchOrchestrator.search()` (Sprint 5),
entièrement en mémoire dans le câblage par défaut du dépôt — les tests
réutilisent donc exactement le même fixture (vidage des caches
`get_research_orchestrator`/`get_kernel`/`get_watch_agent`) que
`tests/integration/agents/test_watch_agent_integration.py`.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `run_watch()` | `get_watch_agent()` (Sprint 36, via `Depends()`) | Une seconde instance de `WatchAgent`, un second chemin de recherche |
| `_parse_case_id()` | Même compromis tolérant que `document/routes.py`/`chat/routes.py` | Une seconde convention de parsing `case_id` |
| `_to_watch_response()` | `WatchResultResponse.model_validate()` (Pydantic) | Un mapping champ par champ dupliquant la forme de `WatchAgent.result` |
| `WatchResponse` | Forme d'`AgentOutput` (même patron que `ContractAnalysisResponse`/`_agent_event_payload`) | Une forme de réponse aplatie ou renommée sans raison |

## Vérification finale

- `ruff check src/tmis/api/v1/watch tests/integration/api/
  test_watch_api.py` → All checks passed.
- `mypy src/tmis/api/v1/watch` (`mypy --strict`) → Success, aucune erreur.
- `pytest -q` (suite complète) → **2210 passed, 7 skipped** (2204
  préexistants + 6 nouveaux), aucune régression.
- Vérification manuelle bout en bout : serveur `uvicorn tmis.main:app`
  démarré localement — `query` seule (résultats nouveaux + alerte
  générée), `connectors` filtré, `known_result_ids` (second appel : `new_
  results` vide, `alert_message` nul, avertissement explicite), `case_id`
  transmis à `ResearchOrchestrator.history`, requête sans `query` → `422`
  natif. Détail complet (requêtes et réponses) dans
  docs/reports/sprint-40-rapport-audit.md.

## Frontend : décision de rester backend-only

Même décision et même raisonnement qu'au Sprint 39 (docs/166) : aucun
écran de veille n'existe à ce jour côté frontend. Ce travail reste pour un
sprint frontend dédié, après que les quatre sprints d'exposition backend
(38 à 41) auront livré une surface d'API stable.

## Confirmation explicite : aucune persistance introduite

`known_result_ids` reste entièrement porté par l'appelant, exactement
comme au Sprint 36 : ce sprint ne lit ni n'écrit aucun store nommé
« veille », aucune table, aucun `WatchStorePort`. La décision du Sprint 36
(docs/164, Question Ouverte n°1 de ce sprint-là) n'est pas rouverte — elle
n'a même pas eu besoin de l'être, la Phase 0 de ce sprint n'ayant identifié
aucun besoin réel de persistance pour que l'exposition soit utilisable
(voir docs/167 et la question ouverte n°1 ci-dessus).
