# Rapport d'audit — Sprint 40 (Exposition de `WatchAgent`)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« PHASE 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), l'état
réel des six éléments désignés par la mission, confirme qu'aucun n'a
changé de forme depuis son sprint d'origine, documente le raisonnement
derrière les deux questions ouvertes tranchées avant tout code, et clôt
sur une vérification manuelle bout en bout menée contre un vrai serveur
`uvicorn`.

## Éléments désignés par le prompt : forme confirmée, aucun écart

| Élément | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `backend/src/tmis/agents/watch_agent.py` | `context["query"]` obligatoire (sinon `AgentOutput` dégradé, `ConfidenceLevel.LOW`, avertissement, aucune recherche lancée) ; `context["connectors"]` (`list[str] \| None`) et `context["known_result_ids"]` (`list[str]`, fourni par l'appelant) optionnels ; `AgentInput.case_id` optionnel ; `result = {search_id, query, connectors_used, result_ids, new_results, alert_message, model}` | Confirmé exact, ligne par ligne (voir `WatchAgent.run()`, lignes 77-144) |
| `backend/src/tmis/agents/bootstrap.py` | `get_watch_agent()` (`@lru_cache`), déjà câblé sur `ResearchOrchestrator`/`TMISKernel`/`AIIntelligenceFabric`/`AIGovernancePlatform` (Sprint 36) | Confirmé exact — **non modifié**, consommé via `Depends()` |
| `backend/src/tmis/api/v1/case_intelligence/routes.py` | Patron de ressource imbriquée sous un dossier : chaque route suppose un `CaseProfile` déjà créé, 404 sinon (`_get_profile_or_404`) | Confirmé exact — sert de contre-exemple direct pour la Question 1 (voir ci-dessous) |
| `backend/src/tmis/api/v1/document/routes.py` | Patron de ressource imbriquée sous un document (`GET /{document_id}/analysis`, Sprint 39), même mécanique 404/409 préalable | Confirmé exact — sert de contre-exemple direct pour la Question 1 |
| `backend/src/tmis/api/v1/chat/routes.py` | Patron des modes de chat (Sprint 33/38) : `mode: Literal["general", "research", "jurisprudence"]`, chaque mode single-shot lisant `context["query"]` depuis `ChatMessageRequest.message: str`, un champ scalaire unique | Confirmé exact — aucun mode existant ne transporte de liste, ce qui exclut le chat comme point d'ancrage pour une configuration de veille à plusieurs listes |
| Absence de précédent `GET` + paramètre liste | Recherche exhaustive de tous les `@router.get(...)` du dépôt | Confirmée — voir ci-dessous |

Aucun de ces éléments n'avait un contenu différent de celui attendu par
la mission — aucun arrêt nécessaire, le code a pu commencer directement
une fois les deux questions ouvertes tranchées.

## Recherche exhaustive : aucun `GET` existant n'accepte de paramètre liste

```
$ grep -rn "@router\.\(get\|post\|patch\|delete\)" backend/src/tmis/api/v1/*/routes.py
document/routes.py:89:@router.post("/upload", ...)
document/routes.py:117:@router.get("/{document_id}", ...)
document/routes.py:131:@router.get("/{document_id}/versions", ...)
document/routes.py:160:@router.get("/{document_id}/analysis", ...)
case/routes.py:24:@router.post("", ...)
case/routes.py:35:@router.get("", ...)
chat/routes.py:123:@router.post("/stream")
health/routes.py:6:@router.get("")
case_intelligence/routes.py:61:@router.post("/{case_id}/profile", ...)
case_intelligence/routes.py:71:@router.get("/{case_id}/profile", ...)
case_intelligence/routes.py:78:@router.patch("/{case_id}/profile", ...)
case_intelligence/routes.py:92:@router.delete("/{case_id}/profile", ...)
case_intelligence/routes.py:102:@router.get("/{case_id}/timeline", ...)
case_intelligence/routes.py:118:@router.get("/{case_id}/summary", ...)
case_intelligence/routes.py:133:@router.get("/{case_id}/search", ...)
```

Chaque signature de `GET` a été relue directement : les seuls paramètres
de requête observés sont `q: str` (`/cases/{case_id}/search`),
`domain: LegalDomain | None`, `compare_document_id: str | None`,
`case_id: str | None` (`/documents/{document_id}/analysis`) — tous
scalaires. Aucun `list[str]` n'apparaît dans la signature d'aucun `GET`
existant. Cette absence confirme exactement ce que la mission annonçait
et a directement informé la décision sur la Question Ouverte n°2 (voir
docs/167-architecture-exposition-agent-veille.md et le rapport
d'architecture).

## Question Ouverte n°1 — Rattachement

**Décision : (a) — `POST /watches`, `case_id` optionnel dans le corps de
la requête.** Voir docs/167-architecture-exposition-agent-veille.md pour
le raisonnement complet ; en résumé, les deux ressources imbriquées
existantes exigent toutes les deux qu'une ressource au segment de chemin
existe déjà (404 préalable) — une contrainte que `WatchAgent` n'impose
jamais sur `case_id` (aucun appel à un `CaseStorePort`). `ResearchAgent`
(même optionnalité de `case_id`, exposé au Sprint 33) n'a jamais été
rattaché à un dossier dans son URL non plus — `WatchAgent` suit le même
principe.

## Question Ouverte n°2 — Verbe HTTP

**Décision : `POST`.** Confirmée par la recherche exhaustive ci-dessus —
aucun `GET` existant n'accepte de paramètre liste, et `connectors`/
`known_result_ids` sont tous deux des listes. Voir
docs/167-architecture-exposition-agent-veille.md pour le raisonnement
complet.

## Confirmation explicite : aucune signature de contrat modifiée

- `AgentInput`/`AgentOutput`/`AgentPort` (`tmis.ai.schemas.agent`) :
  **aucune ligne modifiée**.
- `WatchAgent` (`agents/watch_agent.py`) : **aucune ligne modifiée** —
  consommé tel quel via `get_watch_agent()`.
- `get_watch_agent()` (`agents/bootstrap.py`) : **aucune ligne modifiée**.
- `ResearchOrchestrator`, `AIIntelligenceFabric`, `TMISKernel`,
  `AIGovernancePlatform` : **aucune ligne modifiée**.
- `Orchestrator`, `ContractAgent`, `ResearchAgent`, `JurisprudenceAgent` :
  **non touchés**, hors périmètre de ce sprint (voir mission).
- `case_intelligence/routes.py`, `document/routes.py`, `chat/routes.py` :
  **aucune ligne modifiée** — lus pour confirmation des patrons
  existants, jamais écrits.
- Aucun `WatchStorePort` ni équivalent introduit : `known_result_ids`
  reste entièrement porté par l'appelant (voir confirmation explicite
  dans le rapport d'architecture).

## Résultat des tests

- Backend : `pytest -q` — **2210 passed, 7 skipped** (2204 préexistants +
  6 nouveaux dans `tests/integration/api/test_watch_api.py`), aucune
  régression.
- `ruff check src/tmis/api/v1/watch tests/integration/api/
  test_watch_api.py` → All checks passed.
- `mypy src/tmis/api/v1/watch` (le dépôt est en `mypy --strict`) →
  Success, aucune erreur.

## Vérification manuelle bout en bout

Serveur `uvicorn tmis.main:app` démarré localement (`ResearchOrchestrator`
étant entièrement en mémoire dans le câblage par défaut du dépôt, aucune
base PostgreSQL n'était nécessaire pour cette vérification, contrairement
au Sprint 39) :

```
$ curl -X POST http://127.0.0.1:8010/api/v1/watches \
  -H "Content-Type: application/json" \
  -d '{"query": "responsabilité contractuelle", "connectors": ["jurisprudence"]}'
200 {"result":{"search_id":"5419f958-...","query":"responsabilité contractuelle",
"connectors_used":["jurisprudence"],"result_ids":["cass-civ1-2019-01"],
"new_results":[{"id":"cass-civ1-2019-01","title":"Cass. civ. 1re, 12 janvier 2019",
"excerpt":"Décision de principe sur la responsabilité contractuelle en cas
d'inexécution.","connector":"jurisprudence","document_type":"jurisprudence",
"reference":"Cour de cassation","date":null,"score":0.698...},
"alert_message":"[anthropic:claude-sonnet-5] Rédige une alerte de veille
juridique pour la requête 'responsabilité contractuelle' : 1 nouveau(x)
résultat(s) depuis la dernière exécution de cette veille.\n- Cass. civ. 1re,
12 janvier 2019 (jurisprudence, Cour de cassation) : Décision de principe...",
"model":"claude-legal"},"citations":[{"source_id":"cass-civ1-2019-01",
"connector":"jurisprudence", ...}],"confidence":"medium","warnings":[]}

$ curl -X POST http://127.0.0.1:8010/api/v1/watches -d '{}'
422 {"detail":[{"type":"missing","loc":["body","query"], ...}]}

$ curl -X POST http://127.0.0.1:8010/api/v1/watches \
  -d '{"query": "responsabilité contractuelle", "connectors": ["jurisprudence"],
      "known_result_ids": ["cass-civ1-2019-01"]}'
200 {"result":{... "new_results":[],"alert_message":null,"model":null},
"citations":[],"confidence":"high",
"warnings":["No new result since the last watch run for query
'responsabilité contractuelle': 1 already-known result(s)."]}

$ curl -X POST http://127.0.0.1:8010/api/v1/watches \
  -d '{"query": "clause de non-concurrence",
      "case_id": "11111111-1111-1111-1111-111111111111"}'
200
```

Tous les comportements attendus ont été observés directement contre le
serveur réel : recherche filtrée par connecteur avec alerte réellement
générée par `TMISKernel.complete()`, `422` natif de FastAPI/Pydantic sur
`query` manquant, exclusion correcte des `known_result_ids` déjà vus sur
un second appel (avec confiance `HIGH` reflétant le cache hit de
`ResearchOrchestrator`, `alert_message` nul et `citations` vide comme
attendu quand `new_results` est vide), et transmission de `case_id` sans
erreur. Serveur arrêté proprement en fin de vérification.

## Conclusion

Aucun des six éléments désignés par le prompt n'avait un contenu
différent de celui attendu. Les deux questions ouvertes ont été tranchées
en Phase 0 avant tout code et documentées dans
docs/167-architecture-exposition-agent-veille.md et le rapport
d'architecture. Aucune découverte de comportement inattendu n'a eu lieu
(contrairement au Sprint 39) : les six éléments correspondaient
exactement à ce qui était annoncé par la mission, et la recherche
exhaustive sur les `GET` existants a confirmé, sans exception, l'absence
de précédent invoquée par la Question Ouverte n°2.
