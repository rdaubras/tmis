# Rapport d'audit — Sprint 38 (Exposition de `JurisprudenceAgent` dans le chat)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« PHASE 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), l'état
réel des cinq fichiers désignés par la mission, confirme qu'aucun n'a
changé de forme depuis son sprint d'origine, et documente deux
découvertes faites en cours de mise en œuvre (une sur les données de
fixture du connecteur jurisprudence, une sur l'environnement de
vérification manuelle).

## Fichiers désignés par le prompt : forme confirmée, aucun écart

| Fichier | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `backend/src/tmis/api/v1/chat/schemas.py` | `ChatMessageRequest.mode: Literal["general", "research"] = "general"` | Confirmé exact — un seul littéral à étendre, comme annoncé |
| `backend/src/tmis/api/v1/chat/routes.py` | `_research_agent_input()`, `_research_event_payload()`, `_research_summary_text()`, branche `mode == "research"` dans `stream_chat()` (Sprint 33) | Confirmé exact — voir décision de généralisation/duplication ci-dessous |
| `backend/src/tmis/agents/jurisprudence_agent.py` | `JurisprudenceAgent.run()` lit `agent_input.context["query"]` et `agent_input.case_id` ; `result` = mêmes clés que `ResearchAgent.result` (`search_id`, `query`, `results`, `connectors_used`, `duration_ms`, `cache_hit`) plus `comparison: str \| None` et `model: str \| None` | Confirmé exact — **CTO validé en Phase 0** : sur-ensemble strict de `ResearchAgent.result`, non modifié par ce sprint |
| `backend/src/tmis/agents/bootstrap.py` | `get_jurisprudence_agent()` (`@lru_cache`), déjà câblé sur `ResearchOrchestrator`/`TMISKernel`/`AIIntelligenceFabric`/`CaseStorePort`/`AIGovernancePlatform` (Sprint 34) | Confirmé exact — **non modifié**, consommé via `Depends()` exactement comme `get_research_agent()` |
| `frontend/src/app/(app)/chat/page.tsx` | `ChatMode = "general" \| "research"`, bouton bascule (`variant`/`aria-pressed`), rendu conditionnel `message.research ? <ResearchResults .../> : ...`, composant `ResearchResults` | Confirmé exact — patron reproduit à l'identique pour le troisième mode |
| `docs/161-architecture-agent-recherche.md` | Style de référence : vue d'ensemble Mermaid, sections Phase 1/2/3, section de vérification manuelle bout-en-bout Playwright | Confirmé, utilisé comme gabarit direct pour docs/165 |

Aucun de ces fichiers n'avait un contenu différent de celui attendu par
la mission — aucun arrêt nécessaire, le code a pu commencer directement.

## Décision Phase 0 : généraliser deux fonctions, dupliquer la troisième

La mission demandait explicitement de trancher entre généraliser et
dupliquer `_research_agent_input`/`_research_event_payload`/
`_research_summary_text`, et de documenter le choix (voir
docs/165-architecture-exposition-agent-jurisprudence.md, section Phase 1,
pour le détail complet) :

- `_research_agent_input` (renommée `_agent_input`) et
  `_research_event_payload` (renommée `_agent_event_payload`) ne
  contiennent, à la lecture, **aucune ligne spécifique au mode
  recherche** — généralisées et réutilisées telles quelles par les deux
  modes single-shot.
- `_research_summary_text` porte un vocabulaire propre au mode recherche
  ("Recherche juridique : ... resultat(s) trouve(s)") — **dupliquée** en
  `_jurisprudence_summary_text` ("Comparaison de jurisprudence : ...
  decision(s) comparee(s)") plutôt que paramétrée par un `label`, qui
  n'aurait fait que déplacer la différence dans un argument.

Le corps de branchement (persister le tour utilisateur, exécuter l'agent
une fois, persister le résumé, renvoyer un unique événement SSE),
strictement identique entre les deux modes, est extrait en
`_run_single_shot_agent_mode()`, paramétrée par l'agent (typé `AgentPort`,
le contrat déjà partagé par tous les agents de `tmis.agents`) et la
fonction de résumé — `mode == "research"` reste, lui, un appel de trois
lignes à cette fonction partagée, comportement inchangé.

## Décision Phase 0 : `ResearchResults` étendu d'une prop, pas de composant dérivé

`JurisprudenceAgent.result` étant un sur-ensemble strict de
`ResearchAgent.result` (confirmé ci-dessus), la mission n'imposait pas de
composant séparé. `ResearchPayload.result` gagne deux champs optionnels
(`comparison?: string | null`, `model?: string | null`) et
`ResearchResults` affiche un bloc de synthèse quand `comparison` est
présent — aucun nouveau composant, aucune nouvelle primitive `ui/`.

## Découverte en cours d'implémentation : la fixture du connecteur jurisprudence est un texte accentué unique

`tmis.ai.connectors.jurisprudence_connector._FIXTURE` ne contient qu'une
seule décision, dont le contenu ("Décision de principe sur la
responsabilité contractuelle...") porte des accents, et
`tmis.ai.connectors._fixture_search.search_fixture()` fait une recherche
de sous-chaîne insensible à la casse mais **sensible aux accents**. Les
requêtes de test initiales ("clause de non-concurrence", puis
"responsabilite contractuelle" sans accent) ne matchaient donc aucun
résultat. **Décision** : les tests d'intégration du mode `"jurisprudence"`
utilisent la requête `"contractuelle"` (sans accent, sous-chaîne directe
du contenu de la fixture) — même contrainte que les tests du mode
`"research"` existants, qui utilisent déjà `"contrat de travail"` pour la
même raison sur le connecteur codes. Aucune modification de la fixture ni
de `search_fixture()` : ce sont des composants du Sprint 2/16, hors
périmètre de ce sprint.

## Découverte en cours de vérification manuelle : hydratation React indisponible dans cet environnement de session

La vérification manuelle bout-en-bout (voir
docs/165-architecture-exposition-agent-jurisprudence.md) a confirmé le
comportement serveur par `curl` (un seul événement SSE, `comparison`
correctement peuplé) mais n'a pas pu observer la bascule du bouton
« Jurisprudence » piloté par Playwright/Chromium : aucun clic ne
déclenche de mise à jour d'état React. Investigation menée avant de
conclure à une régression : chunks JS servis en 200, aucune erreur
console/page, comportement identique avec Turbopack et
`next dev --webpack`, et **identique sur `/dashboard`**, une page non
touchée par ce sprint — l'hydratation n'aboutit sur aucune page de
l'application dans cette session. Conclusion : limite de l'environnement
d'exécution, pas un défaut introduit par ce sprint. La non-régression du
rendu (`ResearchResults`, toggle, textes conditionnels) reste, elle,
vérifiée par lecture directe du JSX modifié, `tsc --noEmit`, `next build`
et `eslint`, tous verts.

## Confirmation explicite : aucune signature de contrat modifiée

- `AgentInput`/`AgentOutput`/`AgentPort` (`tmis.ai.schemas.agent`) :
  **aucune ligne modifiée**.
- `JurisprudenceAgent` (`agents/jurisprudence_agent.py`) : **aucune ligne
  modifiée** — consommé tel quel via `get_jurisprudence_agent()`.
- `get_jurisprudence_agent()` (`agents/bootstrap.py`) : **aucune ligne
  modifiée**.
- `ResearchOrchestrator.search()`, son pipeline interne, `ClauseEngine`,
  `AIIntelligenceFabric`, `AIGovernancePlatform` : **aucune ligne
  modifiée**.
- `ContractAgent`, `WatchAgent`, `Orchestrator`, leurs bootstraps : **non
  touchés**, hors périmètre de ce sprint (voir mission).
- Mode `"general"` de `stream_chat()` : **aucune ligne modifiée** — le
  bloc `history`/`_build_prompt`/`kernel.complete_stream()` est
  syntaxiquement inchangé.
- Mode `"research"` de `stream_chat()` : la branche appelle désormais
  `_run_single_shot_agent_mode()` au lieu d'un bloc dupliqué, mais avec
  exactement le même agent, la même fonction de résumé
  (`_research_summary_text`, non modifiée) et la même construction
  d'événement SSE — comportement observable bit-à-bit identique,
  vérifié par les 6 tests d'intégration existants sur ce mode, tous
  restés verts sans modification de leurs assertions.

## Résultat des tests

- Backend : `pytest -q` — **2192 passed, 7 skipped** (suite complète,
  aucune régression).
- Frontend : `tsc --noEmit`, `next build`, `eslint` — tous verts, aucune
  erreur ni avertissement nouveau sur `(app)/chat/page.tsx`.

## Conclusion

Aucun des fichiers désignés par le prompt n'avait un contenu différent de
celui attendu. Les deux décisions de conception demandées par la mission
(généraliser vs dupliquer les fonctions de chat ; prop optionnelle vs
composant dérivé côté frontend) ont été tranchées en Phase 0 avant tout
code et documentées ci-dessus et dans le rapport d'architecture. Deux
découvertes ont été faites en cours de travail — une sur les données de
fixture du connecteur jurisprudence (résolue en adaptant la requête de
test, aucun composant modifié), une sur une limite de l'environnement de
vérification manuelle (signalée, sans impact sur le code livré ni sur les
tests automatisés, tous verts).
