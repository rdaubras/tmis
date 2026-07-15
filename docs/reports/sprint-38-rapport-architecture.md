# Rapport d'architecture — Sprint 38 (Exposition de `JurisprudenceAgent` dans le chat)

## Résumé

Le Sprint 38 étend le chat (`/api/v1/chat/stream`, Sprint 32 mode
`"general"`, Sprint 33 mode `"research"`) d'un troisième mode,
`"jurisprudence"`, câblé sur `JurisprudenceAgent` — réel depuis le
Sprint 34, non modifié par ce sprint. La Phase 0 de re-audit
(docs/reports/sprint-38-rapport-audit.md) a confirmé que les cinq
fichiers désignés avaient le contenu attendu et a tranché deux décisions
de conception explicitement laissées ouvertes par la mission avant tout
code.

Périmètre livré : `tmis/api/v1/chat/schemas.py` (littéral additif
`"jurisprudence"`), `tmis/api/v1/chat/routes.py` (généralisation de deux
fonctions Sprint 33, duplication minimale d'une troisième, nouvelle
fonction partagée `_run_single_shot_agent_mode`, nouvelle branche
`mode == "jurisprudence"`), `frontend/src/app/(app)/chat/page.tsx`
(deuxième bouton bascule, `ResearchPayload`/`ResearchResults` étendus de
deux champs optionnels), 5 tests backend nouveaux, 0 test existant
modifié, docs/165-architecture-exposition-agent-jurisprudence.md, note de
révision dans docs/09-roadmap-30-sprints.md.

**Aucun autre agent touché. `JurisprudenceAgent`, `ResearchOrchestrator`
et son pipeline interne non modifiés. Zéro changement de signature sur
`AgentInput`/`AgentOutput`/`AgentPort`/`JurisprudenceAgent.run()`/
`ChatMessageRequest` (hors extension additive du littéral `mode`).**

## Décisions structurantes

### Généraliser `_research_agent_input`/`_research_event_payload`, dupliquer `_research_summary_text`

La mission demandait de trancher explicitement, pas de choisir un patron
par défaut. Critère retenu : une fonction ne contenant, à la lecture,
**aucune ligne dépendant du mode appelant** est généralisée sans risque —
la dupliquer n'ajouterait rien d'autre qu'un second nom à maintenir en
synchronisation avec le premier. Une fonction dont le contenu **est** le
vocabulaire d'un mode donné (un texte en français destiné à
`ConversationMemory`) est dupliquée, parce que la paramétrer par un
argument de type `label`/`noun` ne ferait que déplacer la différence
réelle dans un troisième endroit sans rien supprimer.

Appliqué :

- `_research_agent_input(payload)` → `_agent_input(payload)` : construit
  `AgentInput(task_id=uuid.uuid4(), case_id=case_uuid,
  context={"query": payload.message})`. Ni `ResearchAgent` ni
  `JurisprudenceAgent` ne distinguent la provenance de cet `AgentInput` —
  les deux lisent `context["query"]` (Sprint 33 et Sprint 34,
  respectivement) et le même `case_id`. Renommée pour ne plus laisser
  croire qu'elle est spécifique à la recherche ; comportement
  **strictement identique**, vérifié par les 6 tests de recherche
  préexistants restés verts sans modification de leurs assertions.
- `_research_event_payload(output)` → `_agent_event_payload(output)` :
  sérialise `output.result` tel quel dans le payload SSE — cette fonction
  n'a jamais eu besoin de connaître les clés de `result` pour les
  transmettre, donc l'ajout de `comparison`/`model` par
  `JurisprudenceAgent` ne lui demande aucune modification.
- `_research_summary_text(output)` : **conservée sans modification**
  (même nom, même comportement, même texte "Recherche juridique : ...").
  `_jurisprudence_summary_text(output)` est une fonction séparée,
  structurellement identique (compte + jusqu'à 3 titres) mais avec un
  vocabulaire propre ("Comparaison de jurisprudence : ... decision(s)
  comparee(s)").

Le corps de branchement commun aux deux modes single-shot — persister le
tour utilisateur, exécuter l'agent une seule fois (jamais de streaming
token par token : le résultat est déjà entièrement calculé), persister le
résumé, renvoyer un unique événement SSE suivi de `event: done` — est
extrait en `_run_single_shot_agent_mode(payload, kernel, agent,
summary_text)`, typée `agent: AgentPort` (le contrat déjà partagé par
tous les agents de `tmis.agents`, `tmis.ai.schemas.agent.AgentPort`,
jamais un type ad hoc). `mode == "research"` et `mode == "jurisprudence"`
deviennent chacun un appel de trois lignes à cette fonction partagée :

```python
if payload.mode == "research":
    return await _run_single_shot_agent_mode(
        payload, kernel, research_agent, _research_summary_text
    )

if payload.mode == "jurisprudence":
    return await _run_single_shot_agent_mode(
        payload, kernel, jurisprudence_agent, _jurisprudence_summary_text
    )
```

Alternative rejetée : dupliquer intégralement le bloc de la branche
`"research"` pour la branche `"jurisprudence"` (patron suivi par
`_research_summary_text`/`_jurisprudence_summary_text`, mais appliqué ici
à un bloc de dix lignes plutôt qu'à un texte de deux lignes) — aurait
laissé deux copies du même enchaînement `add_message` ->
`agent.run()` -> `add_message` -> `StreamingResponse` à maintenir en
synchronisation, pour un bloc qui ne diffère par aucune ligne entre les
deux modes.

### `ChatMessageRequest.mode: Literal["general", "research", "jurisprudence"] = "general"`

Extension additive du littéral existant, défaut inchangé : tout appelant
qui ignore ce champ garde exactement le comportement d'avant ce sprint —
même principe que l'ajout de `"research"` au Sprint 33.

### Frontend : `ResearchPayload.result` étendu de deux champs optionnels, aucun composant dérivé

`JurisprudenceAgent.result` est un sur-ensemble strict de
`ResearchAgent.result` (confirmé en Phase 0, lecture directe de
`jurisprudence_agent.py::run()`) : mêmes clés
(`search_id`/`query`/`results`/`connectors_used`/`duration_ms`/
`cache_hit`) plus `comparison: str | None` et `model: str | None`. La
divergence de forme entre les deux agents est donc purement additive, pas
structurelle — un critère explicite de la mission pour choisir entre
« composant dérivé » et « prop optionnelle ».

**Décision** : `ResearchPayload.result` gagne
`comparison?: string | null` et `model?: string | null`.
`ResearchResults` affiche un bloc de synthèse (texte de la comparaison +
nom du modèle, dans le même style de carte que chaque résultat) quand
`result.comparison` est défini, positionné après les avertissements et
avant la liste des décisions — la synthèse répond à la question posée
avant de lister les décisions qui la soutiennent. Le champ
`message.research` et le nom du composant `ResearchResults` sont
**conservés à l'identique** pour le mode jurisprudence plutôt que
renommés en quelque chose de plus générique : même précédent que le
backend, qui réutilise `ResearchResult`/`ResearchCitation` (les types de
la LRE) sans les renommer alors que `JurisprudenceAgent` les consomme
aussi depuis le Sprint 34.

Un second bouton bascule, `"Jurisprudence"`, rejoint `"Recherche
juridique"` avec le même patron exact (`variant`/`aria-pressed`/logique
de bascule vers `"general"`). `SINGLE_SHOT_MODES = ["research",
"jurisprudence"]` remplace, côté logique de requête (lecture de la
réponse en un seul bloc, `streaming` initial), les vérifications
`mode === "research"` — les textes propres à chaque mode (placeholder,
libellé du bouton d'envoi) restent des branches explicites par mode,
comme c'était déjà le cas.

## Bug corrigé en cours d'implémentation, hors du champ initial du diff

Aucun — ce sprint n'a touché aucun code préexistant en dehors des points
listés ci-dessus (extension additive de `ChatMessageRequest`/
`stream_chat`, extension additive de `ResearchPayload`/`ResearchResults`
côté frontend). Aucune régression, aucun comportement préexistant
modifié.

## Test existant modifié : aucun

Les 2187 tests préexistants (Sprints 32 à 37 inclus) passent tous sans
modification — vérifié par exécution complète (`pytest -q`, 2192 passed,
7 skipped). 5 tests nouveaux dans
`tests/integration/ai/test_chat_api_integration.py` :

- `test_chat_stream_jurisprudence_mode_returns_a_single_event_with_comparison` :
  un seul événement SSE, `result.connectors_used == ["jurisprudence"]`,
  `comparison`/`model` présents dans `result`, citations alignées sur les
  résultats.
- `test_chat_stream_jurisprudence_mode_with_no_result_still_returns_a_clean_event` :
  requête sans résultat -> `results: []`, `comparison: None`,
  `confidence: "low"`, `citations: []` — même patron que le test
  équivalent en mode recherche.
- `test_chat_stream_jurisprudence_mode_with_a_non_uuid_case_id_still_searches` :
  un `case_id` qui ne parse pas comme UUID n'empêche pas la comparaison
  (même dégradation gracieuse que le mode recherche, Sprint 33).
- `test_chat_stream_jurisprudence_mode_persists_the_turn` : le tour
  utilisateur et un résumé `"assistant: Comparaison de jurisprudence..."`
  sont bien persistés dans `ConversationMemory`.
- `test_chat_stream_with_unknown_case_id_returns_404_for_jurisprudence_mode` :
  la validation partagée (`case_id` existence) s'applique aussi au
  nouveau mode.

Aucun test n'utilise `app.dependency_overrides` — `JurisprudenceAgent` est
consommé via le singleton `get_jurisprudence_agent()` réel, même patron
que `research_agent`/`get_kernel()`/`get_case_intelligence_workflow()`
déjà en place.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `_run_single_shot_agent_mode` | `AgentPort.run()` (contrat partagé), `ConversationMemory` (même store que les deux autres modes) | Un second store de conversation, un second parseur/générateur SSE |
| `_agent_input`/`_agent_event_payload` (généralisées) | Rien de nouveau — même construction `AgentInput`/même sérialisation `AgentOutput` qu'au Sprint 33 | Une seconde convention de contexte ou de payload SSE |
| `_jurisprudence_summary_text` | Même structure que `_research_summary_text` (compte + titres) | `ConversationMemory` elle-même, toujours une liste de chaînes `"role: content"` |
| `stream_chat` (branche jurisprudence) | `get_jurisprudence_agent()` (Sprint 34, singleton `@lru_cache` inchangé) | Un second bootstrap ou une seconde instance de `JurisprudenceAgent` |
| `frontend/(app)/chat/page.tsx` (`ResearchResults` étendu) | `ResearchPayload`/`Button`/`Card`/`cn()` (Sprint 33) | Un nouveau composant, une nouvelle primitive `ui/` |

## Vérification finale

- `ruff check src/tmis/api/v1/chat tests/integration/ai/test_chat_api_integration.py` → All checks passed
- `mypy src/tmis/api/v1/chat` → Success, aucune erreur
- `pytest -q` (suite complète) → **2192 passed, 7 skipped** (2187
  préexistants + 5 nouveaux), aucune régression
- `frontend` : `npx tsc --noEmit` → aucune erreur ; `npm run lint`
  (eslint) → aucune erreur ; `npm run build` → build de production
  réussi, 11 routes générées dont `/chat`
- Vérification manuelle bout en bout (backend `uvicorn` démarré
  localement) : `curl` sur `/api/v1/chat/stream` avec
  `mode: "jurisprudence"` retourne un unique bloc `data:` avec
  `comparison`/`model` renseignés, suivi de `event: done`. La bascule du
  bouton pilotée par Playwright/Chromium n'a, elle, pas pu être observée
  dans cette session — investigation détaillée dans le rapport d'audit et
  docs/165, concluant à une limite de l'environnement d'exécution
  (l'hydratation React n'aboutit sur aucune page de l'application dans
  cette session, y compris une page non touchée par ce sprint), pas à une
  régression de ce sprint.
