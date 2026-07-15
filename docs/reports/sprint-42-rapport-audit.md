# Rapport d'audit — Sprint 42 (`AgentInput.case_id` : `uuid.UUID` → `str`)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« PHASE 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), l'état
réel des fichiers désignés par la mission — établis par l'audit CTO du
Sprint 41 —, confirme qu'aucun n'a changé depuis, cherche activement tout
nouveau consommateur non anticipé, puis clôt sur le résultat des tests.

## Re-audit : les fichiers désignés n'ont pas changé

Grep frais sur `agent_input\.case_id` dans tout `backend/src/tmis`,
comparé un par un au diagnostic du Sprint 41 :

| Fichier | Ligne | Usage confirmé |
|---|---|---|
| `agents/research_agent.py` | 68 | `str(agent_input.case_id) if agent_input.case_id is not None else None` |
| `agents/jurisprudence_agent.py` | 86 | idem |
| `agents/watch_agent.py` | 96 | idem |
| `agents/contract_agent.py` | 184-185, 199-200 | `if agent_input.case_id is not None:` puis `self._case_store.get(str(agent_input.case_id))` ; `f"Case {agent_input.case_id} was not found..."` |
| `agents/analysis_agent.py` | 102-103, 116-117 | idem |
| `agents/synthesis_agent.py` | 77, 84 | `if agent_input.case_id is None:` puis `case_id = str(agent_input.case_id)` |

Aucune méthode spécifique à `uuid.UUID` (`.hex`, `.int`, `.bytes`,
`.version`, `.urn`, etc.) trouvée sur `agent_input.case_id` dans aucun de
ces six fichiers — confirmé exact, le changement de type reste mécanique
et sûr comme annoncé.

## Re-audit : recherche active de nouveaux consommateurs

Grep frais sur `agent_input\.case_id` (ci-dessus) et sur `AgentInput\(`
dans tout `backend/src/tmis`, sans se limiter aux fichiers déjà listés
par la mission :

```
$ grep -rn "AgentInput(" backend/src/tmis
platform_sdk/agent_sdk/base.py:36
api/v1/watch/routes.py:77
api/v1/document/routes.py:188
api/v1/chat/routes.py:53
api/v1/case_intelligence/routes.py:219
ai_team/coordinator/engine.py:134
```

Six points de construction, exactement les cinq annoncés par la mission
(`chat`, `document`, `watch`, `case_intelligence/routes.py`,
`platform_sdk/agent_sdk/base.py`) plus `ai_team/coordinator/engine.py`,
explicitement mis hors périmètre par la mission (`case_id=None`,
compatible tel quel avec le type plus large). **Aucun écart, aucun
septième point d'appel non anticipé.**

## Confirmation détaillée des cinq points d'appel

- `api/v1/chat/routes.py:53` (`_agent_input`) : confirmé — construit tout
  l'`AgentInput` (pas seulement `case_id`), avec un `try/except
  uuid.UUID(payload.case_id)` dégradant vers `None`. Conservé (la fonction
  fait plus qu'un simple parsing de `case_id`), simplifié.
- `api/v1/document/routes.py:188` (`_parse_case_id`) : confirmé — fonction
  dédiée, uniquement `try/except uuid.UUID(case_id)` → `None`. Devient un
  passe-plat trivial une fois le `try/except` retiré : supprimée.
- `api/v1/watch/routes.py:77` (`_parse_case_id`) : même forme, même
  décision : supprimée.
- `api/v1/case_intelligence/routes.py:219` (`_parse_case_id_for_agent`) :
  même forme, même décision : supprimée.
- `platform_sdk/agent_sdk/base.py:36-38` (`BaseAgentPlugin.invoke()`) :
  confirmé — **différent des quatre précédents** : `case_id=uuid.UUID(str(
  payload["case_id"])) if payload.get("case_id") else None` ne rattrape
  aucune exception. Un `payload["case_id"]` non-UUID lève une `ValueError`
  non gérée, faisant échouer tout `invoke()` — un crash, pas une
  dégradation silencieuse comme les quatre routeurs API. Confirmé par
  lecture directe, aucun `try/except` autour de cette ligne ni dans les
  appelants d'`invoke()` (`PluginPort`, testé dans
  `tests/unit/platform_sdk/test_platform_sdk_agent_connector_sdk.py`,
  aucun test existant ne couvrait ce chemin avant ce sprint).

## `ai_team/coordinator/engine.py:135` : confirmé hors périmètre

```python
agent_input = AgentInput(
    task_id=uuid.uuid4(), case_id=None, context=context_slice.content
)
```

Confirmé exact, ligne 134-136 — `case_id` est toujours `None` ici,
compatible tel quel avec `str | None` comme il l'était avec `uuid.UUID |
None`. Aucun changement nécessaire ; l'absence de propagation d'un
`case_id` réel à cet endroit reste, comme la mission le précise
explicitement, hors périmètre de ce sprint.

## Écart trouvé : aucun

Le diagnostic du Sprint 41 se confirme intégralement à la lecture directe
du code en Phase 0 de ce sprint. Aucun fichier de la liste n'a changé de
forme, aucun nouveau consommateur d'`agent_input.case_id` ou nouveau point
de construction d'`AgentInput` n'est apparu depuis. Le code a pu commencer
directement.

## Découverte en cours d'implémentation : tests existants construisant `AgentInput(case_id=uuid.UUID(...))`

Non anticipée par le texte de mission au-delà de la garantie générale
« ça reste valide avec le nouveau type ». La suite pytest complète, lancée
immédiatement après le changement de type et la simplification des six
agents (avant tout ajout de test), révèle 21 échecs — tous dans des tests
qui construisent `AgentInput` avec un objet `uuid.UUID` réel plutôt
qu'une chaîne (`case_id=uuid.UUID(case_id)`, ou `case_id = uuid.uuid4()`
directement) : `CaseStorePort.get()` (`dict[str, CaseProfile]`) et
`InMemoryResearchHistory.list_for_case()` (`e.case_id == case_id`) font
tous deux une comparaison exacte par type — un objet `uuid.UUID` n'est
jamais égal à sa représentation `str`, même de valeur identique. Avant ce
sprint, la conversion `str(agent_input.case_id)` que ce sprint retire
absorbait cette différence de type ; après, elle ne l'absorbe plus.

**Décision** : adapter ces tests plutôt que réintroduire la conversion
retirée — la mission demande explicitement de retirer les `str(...)`
devenus inutiles, et le contrat `AgentInput.case_id: str | None` rend
`case_id=uuid.UUID(...)` un test qui construit une valeur hors-contrat.
21 occurrences corrigées dans 11 fichiers de test (`case_id=uuid.UUID(x)`
→ `case_id=x` ; `case_id = uuid.uuid4()` → `case_id = str(uuid.uuid4())`),
listées en détail dans le rapport d'architecture. Aucune n'a nécessité de
changer l'assertion elle-même — seule la construction de l'entrée change.

## Résultat des tests

- Backend : `pytest -q` (depuis `backend/`) — **2233 passed, 7 skipped**
  (2226 mesurés directement avant l'ajout des 7 nouveaux tests dédiés à ce
  sprint — un par agent des six agents listés, plus un pour
  `platform_sdk/agent_sdk/base.py` — aucune régression sur les 2226
  existants une fois les 21 constructions de test hors-contrat corrigées).
- `ruff check src/ tests/` → All checks passed.
- `mypy src/` (le dépôt est en `mypy --strict`) → Success: no issues found
  in 1899 source files.

## Vérification bout en bout

- `test_analysis_with_a_non_uuid_case_id_now_populates_the_synthesis`
  (`tests/integration/case_intelligence/test_case_analysis_api.py`,
  renommé depuis `test_analysis_with_a_non_uuid_case_id_still_succeeds`
  du Sprint 41, qui vérifiait l'inverse) : un dossier créé via `POST
  /cases/case-1/profile` puis interrogé via `GET /cases/case-1/analysis`
  (sans `document_id`) produit désormais `result["synthesis"][
  "executive_summary"]` **non vide**, une citation `connector ==
  "case_store"`, et plus aucun avertissement « No case_id provided » —
  la preuve directe que la dette du Sprint 41 est corrigée, pas
  déplacée.
- `test_agent_plugin_invoke_no_longer_raises_on_a_non_uuid_case_id`
  (`tests/unit/platform_sdk/test_platform_sdk_agent_connector_sdk.py`) :
  `BaseAgentPlugin.invoke()` appelé avec `{"case_id": "case-1"}` ne lève
  plus de `ValueError` et transmet `"case-1"` tel quel à `AgentInput.
  case_id`.
- Un test par agent (les six listés) confirmant la résolution d'un
  `case_id` non-UUID (`"case-1"`) là où il était auparavant silencieusement
  perdu : `test_analysis_agent_resolves_case_profile_for_a_non_uuid_case_id`,
  `test_contract_agent_uses_case_profile_for_a_non_uuid_case_id`,
  `test_jurisprudence_agent_uses_case_profile_for_a_non_uuid_case_id`,
  `test_synthesis_agent_resolves_case_profile_for_a_non_uuid_case_id`
  (résolution contre `CaseStorePort`) ; `test_research_agent_passes_a_
  non_uuid_case_id_to_orchestrator_history`,
  `test_watch_agent_passes_a_non_uuid_case_id_to_orchestrator_history`
  (transmission tel quel à `ResearchOrchestrator.search()`/son historique,
  ces deux agents ne consultant jamais `CaseStorePort`).

## Conclusion

Les cinq points d'appel désignés par la mission (six agents plus quatre
routeurs API) correspondaient exactement à ce que l'audit du Sprint 41
annonçait — aucun écart trouvé en Phase 0. Le cinquième point d'appel,
`platform_sdk/agent_sdk/base.py`, confirmé comme un vrai changement de
comportement (`ValueError` → dégradation silencieuse) plutôt qu'une
simplification cosmétique. Une découverte non anticipée par le texte de
mission — 21 tests existants construisant `AgentInput` hors du nouveau
contrat (`case_id=uuid.UUID(...)` plutôt qu'une chaîne) — a été corrigée
en adaptant les tests, pas en réintroduisant la conversion que la mission
demande explicitement de retirer. Suite pytest complète verte,
`ruff`/`mypy --strict` verts sur tout le dépôt, aucune régression.
