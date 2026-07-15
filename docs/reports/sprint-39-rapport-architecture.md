# Rapport d'architecture — Sprint 39 (Exposition de `ContractAgent` dans l'API document)

## Résumé

Le Sprint 39 ajoute une quatrième route à l'API document existante
(`/api/v1/documents`, Sprint 26) : `GET /{document_id}/analysis`, câblée
sur `ContractAgent` — réel depuis le Sprint 35, non modifié par ce
sprint. La Phase 0 de re-audit (docs/reports/sprint-39-rapport-audit.md)
a confirmé que les sept fichiers désignés avaient le contenu attendu et
a tranché les deux décisions de conception explicitement laissées
ouvertes par la mission avant tout code.

Périmètre livré : `tmis/api/v1/document/routes.py` (nouvelle route
`analyze_document`, helpers `_parse_case_id`/`_to_analysis_response`),
`tmis/api/v1/document/schemas.py` (`ContractAnalysisResponse` et ses
modèles imbriqués), 12 tests d'intégration nouveaux, 0 test existant
modifié, docs/166-architecture-exposition-agent-contrats.md, note de
révision dans docs/09-roadmap-30-sprints.md.

**Aucun autre agent touché. `ContractAgent`, `ClauseEngine`,
`DocumentStorePort`, `get_contract_agent()` non modifiés. Zéro
changement de signature sur `AgentInput`/`AgentOutput`/`AgentPort`/
`ContractAgent.run()`. `/upload`, `GET /{document_id}`,
`GET /{document_id}/versions`, `process_document_task` inchangés.**

## Décisions structurantes

### Question ouverte 1 : `409` si le document n'est pas `PROCESSED`, pas un ordre sur `OCR_DONE`

La mission demandait de choisir entre laisser tourner l'analyse sur un
document non traité (en comptant sur les `warnings` de l'agent) ou
renvoyer un `409` explicite. La Phase 0 a établi un fait qui change la
nature du choix : `DocumentIntelligencePipeline.process()` ne pose
jamais, en pratique, l'un des statuts intermédiaires (`VALIDATED`,
`SCANNED`, `OCR_DONE`, ...) sur un `DocumentRecord` réel — seuls
`RECEIVED` (à l'upload) et `PROCESSED` (à la fin du pipeline, sur
succès) le sont (voir docs/reports/sprint-39-rapport-audit.md pour la
recherche exhaustive).

**Décision : `409 Conflict` si `record.status is not ProcessingStatus.PROCESSED`.**
Comparer contre `OCR_DONE` littéralement aurait exigé de construire, côté
API, un ordre total sur des valeurs d'énumération que rien d'autre dans
le dépôt ne compare entre elles aujourd'hui — une logique de séquencement
inventée pour l'occasion, sur des états qui ne sont jamais atteints. Le
test d'égalité contre `PROCESSED` capture exactement la même intention
(« `ocr_text` est-il réellement exploitable ») sans introduire cette
logique : c'est la formulation la plus simple qui reste fidèle au
comportement réel du pipeline, pas une simplification qui perdrait de
l'information.

Ce choix est aussi le plus honnête pour un client frontend : sans lui,
une analyse sur un document `RECEIVED` tournerait sur `ocr_text == ""`,
`ClauseEngine.search()` renverrait quand même la bibliothèque du domaine
(non vide), et rien dans `ContractAgent.run()` n'ajoute d'avertissement
spécifique à un texte vide — un client pourrait recevoir une confiance
`MEDIUM`/`HIGH` et une synthèse générée à partir de rien du tout, sans
signal explicite. Le corps du `409` inclut le statut réel du document
(`status='received'`) pour que le client sache exactement quoi attendre
avant de réessayer.

### Question ouverte 2 : `GET`, confirmant le précédent de `GET /cases/{case_id}/summary`

Aucune divergence trouvée en Phase 0 : `GET /cases/{case_id}/summary`
(Sprint 19) déclenche déjà un calcul réel et génératif
(`CaseSummaryGenerator` via `TMISKernel`) sur verbe `GET`, avec un `404`
préalable sur la ressource. `document_id` joue le même rôle de
ressource de chemin ici, `domain`/`compare_document_id`/`case_id` le même
rôle de paramètres de requête optionnels qu'aucun corps de requête
n'aurait mieux représenté. L'opération ne modifie aucun état persistant
(ni `DocumentRecord`, ni aucune autre table) : un `GET`, même coûteux,
reste sémantiquement correct — contrairement à `/upload`, un vrai `POST`
parce qu'il persiste un nouvel enregistrement et déclenche une tâche
Celery.

### `domain` validé par FastAPI/Pydantic, `compare_document_id`/`case_id` laissés à l'agent

`ContractAgent._resolve_domain()` retombe silencieusement sur
`LegalDomain.COMMERCIAL` si la valeur ne parse pas — un comportement
adapté à un appelant interne (`Orchestrator`, futur) qui ne doit jamais
planter. Une route publique a une contrainte différente : `domain` est
typé `LegalDomain | None` directement dans la signature FastAPI, qui
rejette nativement toute valeur hors énumération par un `422` — une
validation de frontière fournie par le framework, pas une logique
dupliquée depuis l'agent.

`compare_document_id` et `case_id`, à l'inverse, ne sont pas vérifiés
avant l'appel à l'agent : `ContractAgent.run()` résout déjà les deux et
rapporte une absence via `warnings` plutôt que de lever une exception.
Ajouter un `404` par-dessus aurait dupliqué ce que l'agent fait déjà,
pour un rôle différent de celui de `case_id` dans
`GET /cases/{case_id}/summary` (où c'est la ressource principale de
l'URL, pas un paramètre optionnel de comparaison/rattachement).
`_parse_case_id()` reprend, pour la conversion `str -> uuid.UUID | None`,
exactement le même compromis tolérant que `tmis.api.v1.chat.
routes._agent_input` (Sprint 32/38, non touché par ce sprint) : un
identifiant qui ne parse pas comme UUID devient `None` plutôt que de
faire échouer la requête.

### Mapping de réponse : `model_validate` plutôt qu'une reconstruction champ par champ

```python
class ContractAnalysisResponse(BaseModel):
    document_id: str
    result: ContractAnalysisResultResponse  # clauses, version_diff, synthesis, model
    citations: list[CitationResponse]
    confidence: str
    warnings: list[str]
```

La forme reprend celle d'`AgentOutput` (`result` imbriqué, `citations`/
`confidence`/`warnings` au niveau supérieur) — le même patron que
`_agent_event_payload()` du chat (Sprint 33/38), qui sérialise
`output.result` tel quel plutôt que de l'aplatir. Alternative rejetée :
reconstruire `ContractAnalysisResultResponse` champ par champ
(`ClauseFindingResponse(**finding) for finding in ...`,
`ContractVersionDiffResponse(**version_diff) if ... else None`) — cette
version passait les tests mais échouait `mypy --strict` (`output.result`
est typé `dict[str, object]` par le contrat `AgentOutput` commun, donc un
`**finding` ou un `.get("clauses", [])` non narrowé reste `object` pour
le vérificateur de types). **Décision** :
`ContractAnalysisResultResponse.model_validate(output.result)` — Pydantic
retrouve la forme réelle (y compris le dictionnaire imbriqué de
`version_diff` et la liste de dictionnaires de `clauses`) sans qu'aucun
nom de champ ne soit redéclaré une seconde fois dans la route, et sans
isinstance-narrowing manuel — `mypy --strict` passe parce que
`model_validate` accepte `Any` par construction.

## Bug corrigé en cours d'implémentation, hors du champ initial du diff

Aucun — ce sprint n'a touché aucun code préexistant en dehors de l'ajout
additif décrit ci-dessus (une nouvelle route, deux nouveaux helpers, de
nouveaux modèles Pydantic). Aucune régression, aucun comportement
préexistant modifié.

## Test existant modifié : aucun

Les 2192 tests préexistants (Sprints 1 à 38 inclus) passent tous sans
modification — vérifié par exécution complète (`pytest -q`, 2204 passed,
7 skipped). 12 tests nouveaux dans
`tests/integration/document_intelligence/test_document_analysis_api.py` :

- `test_analysis_returns_404_for_unknown_document`
- `test_analysis_returns_409_before_processing_completes`
- `test_analysis_of_a_processed_document`
- `test_analysis_accepts_a_domain_query_param`
- `test_analysis_rejects_an_unknown_domain`
- `test_analysis_with_a_valid_compare_document_id`
- `test_analysis_with_an_invalid_compare_document_id_reports_a_warning`
- `test_analysis_with_a_known_case_id`
- `test_analysis_without_case_id`
- `test_upload_route_is_unaffected` (non-régression)
- `test_get_document_route_is_unaffected` (non-régression)
- `test_versions_route_is_unaffected` (non-régression)

Aucun test n'utilise `app.dependency_overrides` — `ContractAgent` est
consommé via le singleton `get_contract_agent()` réel, même patron que
`research_agent`/`jurisprudence_agent`/`get_case_intelligence_workflow()`
déjà en place. Les tests réutilisent le même fixture sqlite fichier
(sync + async, `StaticPool`) que `test_document_upload_api.py`, avec
`get_contract_agent.cache_clear()` ajouté à la liste des caches vidés par
test — nécessaire parce que `ContractAgent` capture `case_store`
(`get_case_intelligence_workflow().case_store`) à la construction, et ce
store doit être celui de la base de test courante, pas un singleton
laissé par un test précédent.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `analyze_document()` | `get_document_store()` (Sprint 26/37, 404/409 préalables), `get_contract_agent()` (Sprint 35/37, via `Depends()`) | Un second accès au store, une seconde instance de `ContractAgent` |
| `_parse_case_id()` | Même compromis tolérant que `chat/routes.py::_agent_input` (Sprint 32/38) | Une seconde convention de parsing `case_id` |
| `_to_analysis_response()` | `ContractAnalysisResultResponse.model_validate()` (Pydantic, aucune ré-déclaration de champ) | Un mapping champ par champ dupliquant la forme de `ContractAgent.result` |
| `ContractAnalysisResponse` | Forme d'`AgentOutput` (même patron que `_agent_event_payload` du chat) | Une forme de réponse aplatie ou renommée sans raison |

## Vérification finale

- `ruff check src/tmis/api/v1/document tests/integration/
  document_intelligence/test_document_analysis_api.py` → All checks
  passed.
- `mypy src/tmis/api/v1/document` (`mypy --strict`) → Success, aucune
  erreur.
- `pytest -q` (suite complète) → **2204 passed, 7 skipped** (2192
  préexistants + 12 nouveaux), aucune régression.
- Vérification manuelle bout en bout : serveur `uvicorn tmis.main:app`
  démarré localement contre une vraie base PostgreSQL (`alembic upgrade
  head` exécuté au préalable) — `404` sur document absent, `409` avec le
  statut réel avant traitement complet, `200` avec synthèse réellement
  générée par `TMISKernel.complete()` une fois le document `PROCESSED`,
  `422` natif sur un `domain` hors énumération, dégradation gracieuse sur
  un `compare_document_id` inexistant, `GET /{document_id}/versions`
  inchangé (deux versions, `received` puis `processed`). Détail complet
  (requêtes et réponses) dans docs/reports/sprint-39-rapport-audit.md.

## Frontend : décision de rester backend-only

`(app)/documents/page.tsx` est un `ModulePlaceholder` (Sprint 5) — aucune
vue de fiche document n'existe à ce jour pour brancher un bouton
« Analyser » proprement. Contrairement à `JurisprudenceAgent` (Sprint
38), qui étendait une page de chat déjà fonctionnelle, il n'y a ici aucun
écran réel dont ce sprint pourrait étendre le patron sans improviser une
première fiche document non rattachée à un flux existant. **Décision** :
ce sprint reste backend-only ; l'écran document (upload, statut,
déclenchement de l'analyse) revient à un sprint frontend dédié, une fois
les quatre sprints d'exposition backend (38 à 41) terminés.
