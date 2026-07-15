# Rapport d'architecture — Sprint 33 (Agent Recherche Documentaire, réel)

## Résumé

Le Sprint 33 relie `ResearchAgent` (placeholder depuis le Sprint 1) au
`ResearchOrchestrator` réel (Sprint 5, la LRE) et l'expose de façon
additive dans le chat du Sprint 32 via un nouveau mode `"research"`. La
Phase 0 de re-audit (docs/reports/sprint-33-rapport-audit.md) a confirmé
que les fichiers désignés avaient le contenu attendu, et a identifié deux
écarts entre la description du prompt et le comportement réel du code,
tranchés avant tout code.

Périmètre livré : `tmis/agents/research_agent.py` (réécrit, placeholder
-> implémentation réelle), `tmis/agents/bootstrap.py` (nouveau,
`get_research_agent()`), `tmis/api/v1/chat/schemas.py` (champ additif
`mode`), `tmis/api/v1/chat/routes.py` (branche additive `mode ==
"research"`), `frontend/src/app/(app)/chat/page.tsx` (bouton bascule +
rendu dédié des résultats sourcés), 14 tests backend nouveaux, 0 test
existant modifié, docs/161-architecture-agent-recherche.md, note de
révision dans docs/09-roadmap-30-sprints.md.

**Aucun autre agent de `tmis.agents` touché. `ResearchOrchestrator` et
son pipeline interne non modifiés. Zéro changement de signature sur
`AgentInput`/`AgentOutput`/`AgentPort`/`ResearchOrchestrator.search()`/
`Citation`/`ResearchCitation`.**

## Décisions structurantes

### `ResearchAgent` ne câble pas `AIIntelligenceFabric` — une lecture stricte du prompt, pas un oubli

Le prompt demande de vérifier `ai_fabric/fabric.py`/`ai_governance/
overview.py` « si applicable à un agent dont le cœur du travail vient
d'un moteur externe plutôt que de `TMISKernel.complete()` directement ».
`AnalysisAgent`/`SynthesisAgent` appellent tous deux `TMISKernel.
complete()` pour une synthèse narrative et utilisent `AIIntelligenceFabric.
route()` pour choisir le modèle de *cet* appel précis.
`ResearchAgent` n'appelle **jamais** `TMISKernel.complete()` : sa seule
tâche est de relayer `ResearchOrchestrator.search()`, qui ne produit
aucun texte généré par ce sprint.

**Décision** : pas de paramètre `fabric` sur `ResearchAgent`. Câbler
`AIIntelligenceFabric` ici aurait ajouté une façade qui ne route jamais
rien — un signal trompeur sur ce que l'agent fait réellement, alors que
`AnalysisAgent` avait déjà établi, au Sprint 29, le principe inverse
(refuser un patron qui ne correspond pas exactement à ce que l'agent
fait, plutôt que l'appliquer par réflexe de cohérence de surface).
`AIGovernancePlatform.explainability`, elle, reste branchée exactement
comme pour les deux agents précédents (`governance: AIGovernancePlatform
| None = None`, `models_used=()` puisqu'aucun modèle n'est appelé par cet
agent) — un rapport consultable est produit pour chaque recherche
(nombre de résultats, connecteurs utilisés, `cache_hit`), vérifié par
test (`test_research_agent_records_explainability_when_governance_is_
wired`).

### L'adaptateur `ResearchCitation -> Citation` exploite l'alignement positionnel de `ResearchOrchestrator.search()`, jamais un second appel au moteur

`ResearchCitation` ne porte aucun champ `connector` ; `Citation` en
exige un. Réimplémenter la logique de citation pour en dériver un aurait
recréé, au moins partiellement, ce que `CitationEngine`/
`ResearchOrchestrator` font déjà — exactement ce que le prompt interdit
(« aucune logique de recherche/classement/cache réimplémentée »).

**Décision** : la Phase 0 a confirmé par lecture directe que
`ResearchOrchestrator.search()` construit `response.results` (des
`ResearchResult`, qui portent `connector`) et la liste de citations
retournée par `get_citations(search_id)` à partir de la *même* liste
`ranked`, dans la *même* méthode, dans le *même* ordre. L'adaptateur
(`ResearchAgent._to_citation`, dans `tmis.agents.research_agent` —
jamais dans `tmis.legal_research.citations`, qui n'a pas à connaître le
contrat `agents`) zippe donc les deux tuples par position
(`zip(response.results, research_citations, strict=True)`) : `connector`
vient du `ResearchResult` correspondant, `source_id`/`excerpt`/
`reference` du `ResearchCitation`. `strict=True` fait échouer bruyamment
un futur désalignement plutôt que produire silencieusement des citations
mal attribuées. `title`/`date` (absents de `Citation` par contrat) ne
sont pas perdus : ils restent dans `AgentOutput.result["results"]`, que
le frontend affiche à côté de chaque citation. Alternative rejetée :
étendre `Citation` d'un champ `connector` calculé différemment, ou
regénérer une citation depuis `ResearchResult` seul — la première viole
« zéro changement de signature », la seconde duplique
`CitationEngine.build()`.

### `context["query"]` — une nouvelle convention de clé, cohérente avec l'existant

Ni `AnalysisAgent` (`context["document_id"]`) ni `SynthesisAgent`
(aucune clé de `context`, seulement `agent_input.case_id`) n'établissent
de convention pour « le texte d'une requête ». `ResearchAgent` introduit
`context["query"]` — un substantif direct, dans le même style que
`"document_id"`, plutôt qu'un nom plus long ou une clé imbriquée. Absence
de query -> résultat vide, `ConfidenceLevel.LOW`, avertissement explicite
— même patron de dégradation gracieuse que `AnalysisAgent` sur
`document_id` manquant/introuvable.

### Confiance : cascade `LOW` (aucun résultat) / `MEDIUM` (résultats frais) / `HIGH` (résultats servis depuis le cache de classement)

Le prompt demande explicitement que `confidence` reflète `cache_hit`/le
nombre de résultats. Cascade retenue, la plus directe possible : aucun
résultat -> `LOW` ; résultats obtenus mais calculés pour la première fois
(`cache_hit=False`) -> `MEDIUM` ; résultats servis depuis
`ResearchCache` (`cache_hit=True`, donc une réponse déjà produite et
stable dans le temps) -> `HIGH`. Vérifié par test
(`test_research_agent_cache_hit_raises_confidence_to_high`,
`test_research_agent_reports_low_confidence_when_the_lre_finds_
nothing`).

### Chat : une branche additive dans `stream_chat()`, jamais une réécriture

`ChatMessageRequest` gagne `mode: Literal["general", "research"] =
"general"` — un champ explicite plutôt qu'une détection d'intention
automatique (le prompt écarte cette dernière explicitement). Le défaut
`"general"` garantit qu'un appelant existant qui ignore ce champ obtient
exactement le comportement Sprint 32.

`stream_chat()` partage la validation (`case_id` existence, guardrails
sur `message`) entre les deux modes, puis se ramifie : `mode ==
"general"` exécute le chemin Sprint 32 **sans une seule ligne modifiée**
(`get_history` -> `_build_prompt` -> `complete_stream()` chunk par
chunk) ; `mode == "research"` persiste le tour utilisateur, appelle
`ResearchAgent.run()` **une seule fois** (pas de boucle de streaming :
il n'y a rien à streamer, la réponse est déjà entièrement calculée avant
le premier octet SSE), persiste un résumé texte du tour assistant
(`_research_summary_text` — jamais les structures `result`/`citations`
brutes, que `ConversationMemory`, une liste de chaînes `"role:
content"`, ne peut pas représenter), puis renvoie un **unique** événement
`data: {"result": ..., "citations": ..., "confidence": ...,
"warnings": ...}` suivi de `event: done` — même framing SSE que le mode
général, un seul événement au lieu de plusieurs chunks. Vérifié par test
(`test_chat_stream_general_mode_still_works_unchanged` : même requête que
les tests Sprint 32, même résultat).

### `AgentInput.case_id: uuid.UUID` vs le `case_id: str` libre de `case_intelligence` — dégradation gracieuse plutôt que rejet

Écart réel entre deux parties déjà existantes du dépôt, découvert en
Phase 0 en construisant `_research_agent_input()` : `AgentInput.case_id`
est typé `uuid.UUID | None` (signature gelée par la contrainte de ce
sprint), alors que tout `case_id` de `case_intelligence`
(`CaseStorePort.get(case_id: str)`, utilisé tel quel par
`api/v1/case_intelligence/routes.py` sans contrainte de format) est une
chaîne libre — un identifiant comme `"case-chat-1"` est un `case_id`
parfaitement valide dans ce sous-système, mais ne parse pas comme UUID.

**Décision** : `_research_agent_input()` tente `uuid.UUID(payload.
case_id)` ; si le format ne correspond pas, l'agent reçoit `case_id=None`
plutôt qu'un rejet de toute la requête en mode recherche. La recherche
s'exécute quand même — elle ne tague simplement pas l'entrée d'historique
de la LRE avec ce dossier. Alternative rejetée : lever un `400` sur tout
`case_id` non-UUID en mode recherche — aurait rendu le mode recherche
plus strict que le mode général sur exactement le même champ d'entrée,
sans qu'aucune partie du prompt ne le demande. Vérifié par test
(`test_chat_stream_research_mode_with_a_non_uuid_case_id_still_
searches`).

### Frontend : un composant dédié pour les résultats sourcés, jamais un flux de texte token par token

`ResearchResults` (nouveau composant, dans la même page) affiche
`confidence` (badge coloré), le nombre de résultats, les avertissements
éventuels, puis chaque résultat avec titre, type de document + date +
référence, extrait et connecteur source. Le message assistant
correspondant porte un champ `research` (le payload SSE complet) plutôt
que du texte accumulé chunk par chunk — la lecture de la réponse en mode
recherche utilise `response.text()` puis extrait le bloc `data:` unique,
jamais la boucle `reader.read()` incrémentale du mode général (il n'y a
qu'un seul événement, pas des chunks à assembler). Aucune nouvelle
primitive `ui/` : `Button` (variante `default`/`outline` pour l'état du
bouton bascule, `aria-pressed`), `Card`/`CardContent`, `cn()` — les mêmes
que le Sprint 32.

## Bug corrigé en cours d'implémentation, hors du champ initial du diff

Aucun — ce sprint n'a touché aucun code préexistant en dehors des points
listés ci-dessus (`ChatMessageRequest`/`stream_chat` étendus de façon
additive, `research_agent.py` réécrit depuis son placeholder). Aucune
régression, aucun comportement préexistant modifié.

## Test existant modifié : aucun

Les 2125 tests préexistants (Sprint 32 inclus) passent tous sans
modification — vérifié par exécution complète. 14 tests nouveaux :

- `tests/unit/agents/test_research_agent.py` (+6, nouveau fichier) :
  absence de `query` -> `LOW`, recherche réelle sur un `ResearchOrchestrator`
  de test (double du patron `test_research_orchestrator.py` existant)
  avec conversion de citations vérifiée champ par champ, cascade de
  confiance sur `cache_hit`, absence de résultat -> `LOW`, transmission
  de `case_id` à l'historique de la LRE, explicabilité enregistrée quand
  `governance` est injecté.
- `tests/integration/agents/test_research_agent_integration.py` (+3,
  nouveau fichier) : bout en bout sur le vrai
  `get_research_orchestrator()` (mêmes connecteurs fixture que
  `test_research_orchestrator_integration.py`), citations converties de
  bout en bout, `case_id` retrouvé dans l'historique réel, requête
  manquante -> résultat vide sans appeler la LRE.
- `tests/integration/ai/test_chat_api_integration.py` (+5) : un seul
  événement SSE avec résultats + citations en mode recherche, aucun
  résultat -> événement propre (`confidence: "low"`, `citations: []`),
  `case_id` non-UUID n'empêche pas la recherche, le tour de recherche est
  bien persisté dans `ConversationMemory` (tour utilisateur + résumé
  assistant), le mode général reste inchangé (même requête, même
  résultat que les tests Sprint 32).

Aucun test n'utilise `app.dependency_overrides` — `ResearchAgent` est
injecté soit directement (tests unitaires/intégration agent), soit via le
singleton `get_research_agent()` réel (test d'API chat), même patron que
`get_kernel()`/`get_case_intelligence_workflow()` déjà en place.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `ResearchAgent` | `ResearchOrchestrator.search()`/`get_citations()` (Sprint 5, inchangés), `AIGovernancePlatform.explainability` (Sprint 15, optionnel) | Le classement, la déduplication, le cache trois couches, les connecteurs — tout reste dans `ResearchOrchestrator` |
| `ResearchAgent._to_citation` | `ResearchResult.connector` + `ResearchCitation` (alignement positionnel déjà garanti par `ResearchOrchestrator.search()`) | `CitationEngine.build()`, jamais dupliqué |
| `tmis.agents.bootstrap.get_research_agent` | `get_research_orchestrator()` (Sprint 5), `get_ai_governance_platform()` (Sprint 15) — même patron `@lru_cache` que les deux | Un second singleton d'orchestrateur ou de plateforme de gouvernance |
| `api.v1.chat.routes.stream_chat` (branche recherche) | `ResearchAgent.run()`, `ConversationMemory` (même store que le mode général) | Un second store de conversation, une seconde validation de dossier, un second parseur SSE côté serveur |
| `frontend/(app)/chat/page.tsx` (`ResearchResults`) | `Button`/`Card`/`cn()` (Sprint 32) | Une nouvelle primitive `ui/`, un second design de bulle |

## Vérification finale

- `ruff check src tests` (commande CI) → All checks passed
- `mypy src` (1895 fichiers, commande CI) → Success, aucune erreur
- `pytest --cov=tmis --cov-fail-under=90` → 2139 tests passants (2125
  préexistants + 14 nouveaux), 7 skipped (préexistants, gatés par
  `TMIS_REDIS_URL`/`TMIS_RUN_MODEL_DOWNLOAD_TESTS`), aucune régression
- Couverture globale : 95.85 % (seuil CI 90 %, comparable au Sprint 32) ;
  code nouveau à 100 % : `agents/research_agent.py`, `agents/bootstrap.py`,
  `api/v1/chat/{routes,schemas}.py`
- `frontend` : `npx tsc --noEmit` → aucune erreur ; `npm run lint`
  (eslint) → aucune erreur ; `npm run build` → build de production
  réussi, 11 routes générées dont `/chat`
- Vérification manuelle bout en bout (backend `uvicorn` + frontend
  `next dev` démarrés localement, pilotés via `curl` et
  Playwright/Chromium) : `curl` sur `/api/v1/chat/stream` avec
  `mode: "research"` retourne un unique bloc `data:` (résultats +
  citations) suivi de `event: done` ; interface `/chat` : bascule du
  bouton « Recherche juridique », requête « contrat de travail »,
  résultats affichés avec titre/référence/extrait/source et badge de
  confiance ; retour au mode général, tour suivant montre que le résumé
  de la recherche précédente a bien été réinjecté dans l'historique
  consommé par `_build_prompt` — captures d'écran archivées, aucune
  erreur console.

## Confirmation explicite de périmètre

- **Seul `ResearchAgent` a été implémenté** — `JurisprudenceAgent`,
  `ContractAgent`, `WatchAgent`, `DraftingAgent`, `StrategyAgent`,
  `CollaborationAgent` restent des placeholders inchangés ; `git diff
  --stat` sur `tmis/agents/` ne montre que `research_agent.py` (réécrit)
  et `bootstrap.py` (nouveau).
- **`ResearchOrchestrator` et son pipeline interne n'ont pas été
  modifiés** — `git diff --stat` sur `tmis/legal_research/` est vide ;
  `ResearchAgent` n'appelle que `search()`/`get_citations()`, les deux
  seules méthodes publiques déjà exposées.
- **Le mode `"general"` du chat fonctionne à l'identique** — les 5 tests
  Sprint 32 de `test_chat_api_integration.py` passent sans modification,
  plus un test explicite supplémentaire
  (`test_chat_stream_general_mode_still_works_unchanged`) rejouant la
  même requête que le Sprint 32 avec le même résultat attendu.
- **Zéro changement de signature** sur `AgentInput`/`AgentOutput`/
  `AgentPort`/`ResearchOrchestrator.search()`/`Citation`/
  `ResearchCitation` — vérifié par `mypy src` (aucune erreur de type sur
  l'ensemble du dépôt) et par l'absence de toute modification des
  fichiers de schémas dans le diff.
