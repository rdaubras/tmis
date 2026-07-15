# Rapport d'audit — Sprint 33 (Agent Recherche Documentaire, réel)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« Phase 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), ce qui
existe déjà pour chacun des fichiers désignés par le prompt, et confirme
qu'aucun n'a changé de forme depuis son sprint d'origine.

## Fichiers désignés par le prompt : forme confirmée, aucun écart de contenu

| Fichier | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `tmis.agents.research_agent.ResearchAgent` | Placeholder Sprint 1 : `name = "research"`, `async def run(agent_input) -> AgentOutput: raise NotImplementedError(...)` | Confirmé exact — remplacé par ce sprint |
| `tmis.agents.orchestrator.Orchestrator` | Graphe LangGraph `analysis -> verifier -> synthesis -> verifier_final -> END` ; docstring documentant explicitement le patron à suivre pour un agent futur (constructeur injectable, closure `run_<name>`, edges) — **`ResearchAgent` n'est câblé sur aucun nœud de ce graphe aujourd'hui**, ni avant ni après ce sprint | Confirmé exact — **non modifié**, conformément à la contrainte « ne modifie ni ResearchOrchestrator ni son pipeline » (le prompt ne demande pas de nœud `"research"` dans ce graphe, seulement l'exposition dans le chat) |
| `tmis.agents.contracts` | Ré-export de `AgentInput`/`AgentOutput`/`AgentPort`/`ConfidenceLevel` depuis `tmis.ai.schemas.agent` | Confirmé exact, aucune modification |
| `tmis.agents.analysis_agent.AnalysisAgent` (patron Sprints 29-31) | Constructeur `kernel`/`document_store`/`case_store`/`fabric`/`governance`/`firm_id`, tous optionnels avec défaut sain ; lecture de `agent_input.context.get("document_id")` ; `AIIntelligenceFabric.route()` pour choisir le modèle d'un appel `TMISKernel.complete()` ; `AIGovernancePlatform.explainability.generate()` optionnel | Confirmé exact — patron de câblage Fabric/Governance réutilisé où applicable (voir écart n°1 ci-dessous pour la partie *non* applicable) |
| `tmis.ai.schemas.agent` (`AgentInput`/`AgentOutput`/`Citation`) | `AgentInput.case_id: uuid.UUID \| None`, `AgentInput.context: dict[str, object]` ; `AgentOutput.result: dict[str, object]`, `citations: list[Citation]`, `confidence: ConfidenceLevel`, `warnings: list[str]` | Confirmé exact — zéro changement de signature |
| `tmis.ai.schemas.citation.Citation` | `frozen`/`slots` : `source_id`, `connector`, `excerpt`, `reference` — **aucun champ `title`/`date`** ; `RetrievedChunk.to_citation(connector, reference)` montre que `connector` est toujours fourni explicitement par l'appelant, jamais déduit | Confirmé exact — le schéma cible de la conversion, zéro changement |
| `tmis.legal_research.search.orchestrator.ResearchOrchestrator` | `search(raw_text, *, filters=None, connector_names=None, weights=None, user_id=None, case_id: str \| None = None) -> ResearchResponse` ; `get_citations(search_id) -> tuple[ResearchCitation, ...] \| None` construit `tuple(citation_engine.build(r) for r in ranked)` **dans le même ordre et à partir de la même liste `ranked`** que `results=tuple(ranked)` sur la `ResearchResponse` | Confirmé exact — **non modifié**, garantie d'alignement positionnel entre `results` et `get_citations()` vérifiée par lecture directe, exploitée par l'adaptateur (voir Phase 1 de docs/161) |
| `tmis.legal_research.search.ports.ResearchSearchPort` | `Protocol.execute(query, *, connector_names=None) -> tuple[list[ConnectorDocument], list[str], dict[str, RelevanceScores]]` | Confirmé exact, non modifié |
| `tmis.legal_research.search.schemas` (`ResearchResult`/`RelevanceScores`/`ResearchResponse`) | `ResearchResult.connector: str` (le nom du connecteur réel, ex. `"codes"`) ; `ResearchResponse.cache_hit: bool` | Confirmé exact — `ResearchResult.connector` est la source retenue pour `Citation.connector` (voir Phase 1 de docs/161) |
| `tmis.legal_research.citations.schemas.ResearchCitation` | `frozen`/`slots` : `source_id`, `title`, `date`, `document_type`, `reference`, `excerpt` — **aucun champ `connector`** | Confirmé exact — écart structurel n°1 ci-dessous |
| `tmis.legal_research.bootstrap.get_research_orchestrator` | `@lru_cache`, singleton process-wide, enregistre les connecteurs LRE sur le `ConnectorManager` du `TMISKernel` partagé (`get_kernel()`) | Confirmé exact — réutilisé tel quel comme défaut du constructeur de `ResearchAgent` |
| `tmis.api.v1.chat.{routes,schemas}` (endpoint Sprint 32) | `ChatMessageRequest(conversation_id, message, case_id=None, provider=None)` ; `stream_chat()` valide `case_id`/guardrails avant de renvoyer la `StreamingResponse`, persiste `"user: ..."` puis délègue à `kernel.complete_stream()`, qui persiste `"assistant: ..."` une fois le flux terminé | Confirmé exact — docstring de `stream_chat()` annonce explicitement « no `ResearchOrchestrator`/LRE, that is Sprint 33 » : le point d'extension attendu par ce sprint |
| `tmis.ai_fabric.fabric.AIIntelligenceFabric` | Façade unique (`router`/`planner`/`critic`/`comparison`/`consensus`/`fusion`), jamais appelée par `TMISKernel` lui-même (confirmé au Sprint 32) | Confirmé exact — écart n°1 ci-dessous : sans appel `TMISKernel.complete()` propre à cet agent, il n'y a rien à router |
| `tmis.ai_governance.overview.AIGovernancePlatform` | `explainability.generate(firm_id, production_id, *, summary, steps_followed, agents_involved=(), models_used=(), documents_consulted=())` | Confirmé exact — branché, `models_used=()` (aucun modèle appelé par cet agent) |
| `frontend/src/app/(app)/chat/page.tsx` (interface Sprint 32) | Client component, un seul champ `caseId`, envoi via `fetch`, lecture `ReadableStream` chunk par chunk, aucune notion de `mode` ni de citations | Confirmé exact — étendu de façon additive (bouton bascule, rendu dédié des résultats sourcés) |

Aucun de ces fichiers n'avait un contenu différent de celui attendu — le
seul travail de Phase 0 a été de confirmer, par lecture directe, deux
écarts entre la description du prompt et le comportement réel du code,
tranchés avant tout code.

## Deux écarts identifiés en Phase 0, tranchés avant tout code

### 1. `AIIntelligenceFabric` n'a rien à router pour cet agent — contrairement à `AnalysisAgent`/`SynthesisAgent`

Le prompt demande de vérifier `ai_fabric/fabric.py`/`ai_governance/
overview.py` « si applicable à un agent dont le cœur du travail vient
d'un moteur externe plutôt que de `TMISKernel.complete()` directement ».
`AnalysisAgent`/`SynthesisAgent` appellent tous deux `TMISKernel.
complete()` eux-mêmes pour une synthèse narrative, et utilisent
`AIIntelligenceFabric.route()` pour choisir le modèle de *cet* appel.
`ResearchAgent` n'appelle **jamais** `TMISKernel.complete()` : la
recherche documentaire (`ResearchOrchestrator.search()` ->
`HybridResearchSearch` -> connecteurs) ne produit ni synthèse narrative
ni aucun autre texte généré par ce sprint.

**Décision** : `ResearchAgent` ne prend pas de paramètre `fabric`. Le
câbler aurait ajouté une façade qui ne route jamais rien — un mensonge
silencieux sur ce que l'agent fait réellement, l'inverse de la
transparence que ce dépôt vise (voir la docstring d'`AnalysisAgent`
expliquant, au Sprint 29, pourquoi `BaseAgentPlugin` n'était pas non plus
applicable). `AIGovernancePlatform.explainability`, en revanche,
s'applique bien : chaque recherche produit un rapport consultable
(nombre de résultats, connecteurs utilisés, `cache_hit`), optionnel
comme pour les deux agents précédents.

### 2. `ResearchCitation` ne porte pas de nom de connecteur — `Citation.connector` doit venir d'ailleurs

Le prompt demande un « adaptateur explicite » de `ResearchCitation` vers
`Citation`. La lecture directe des deux schémas montre que ce n'est pas
un simple renommage de champs : `ResearchCitation` porte `source_id`,
`title`, `date`, `document_type`, `reference`, `excerpt` — **aucun champ
`connector`**, alors que `Citation` en exige un.

**Décision** : exploiter la garantie d'alignement positionnel, confirmée
par lecture directe de `ResearchOrchestrator.search()` —
`response.results` (des `ResearchResult`, qui portent `connector`) et
`get_citations(search_id)` sont construits à partir de la *même* liste
`ranked`, dans le *même* ordre, dans la même méthode. L'adaptateur zippe
donc les deux tuples par position (`zip(response.results,
research_citations, strict=True)`, `strict=True` pour qu'un futur
désalignement entre les deux échoue bruyamment plutôt que de produire des
citations silencieusement mal attribuées) et prend `connector` sur le
`ResearchResult`, le reste sur le `ResearchCitation`. `title`/`date`
(absents de `Citation`) restent disponibles dans
`AgentOutput.result["results"]`, jamais perdus. Voir
docs/161-architecture-agent-recherche.md pour le détail.

## Confirmation explicite : aucun autre agent, aucune modification du LRE

- `JurisprudenceAgent`, `ContractAgent`, `WatchAgent`, `DraftingAgent`,
  `StrategyAgent`, `CollaborationAgent` : **aucune ligne modifiée** —
  `git diff --stat` sur ce sprint ne touche que
  `tmis/agents/research_agent.py` (réécrit) et `tmis/agents/bootstrap.py`
  (nouveau fichier, factory `get_research_agent()`) côté `tmis.agents`.
- `tmis.agents.orchestrator.Orchestrator` : **non modifié** — le prompt
  demande d'exposer la recherche dans le chat, pas d'ajouter un nœud
  `"research"` au graphe LangGraph existant.
- `tmis.legal_research.search.orchestrator.ResearchOrchestrator` et tout
  son pipeline interne (`queries`, `search` (hybrid), `normalization`,
  `ranking`, `citations`, `cache`, `history`, `evaluation`) : **aucune
  ligne modifiée** — vérifié par `git diff --stat` restreint à
  `tmis/legal_research/`, vide.
- `tmis.legal_research.citations.schemas.ResearchCitation` et
  `tmis.ai.schemas.citation.Citation` : **zéro changement de signature**
  — l'adaptateur vit entièrement dans `tmis.agents.research_agent`.
- `POST /api/v1/chat/stream` en mode `"general"` (par défaut) : **inchangé
  à l'identique** — même séquence `get_history` -> `_build_prompt` ->
  `complete_stream()`, vérifié par les 5 tests Sprint 32 existants
  exécutés sans modification et toujours verts, plus un test explicite
  supplémentaire (`test_chat_stream_general_mode_still_works_unchanged`).

## Conclusion

Aucun des fichiers désignés par le prompt n'avait un contenu différent de
celui attendu. Deux écarts entre la description du prompt et le
comportement réel du code (`AIIntelligenceFabric` non applicable à un
agent qui n'appelle jamais `TMISKernel.complete()`, absence de champ
`connector` sur `ResearchCitation`) ont été identifiés dès la Phase 0,
tranchés avant tout code et documentés ci-dessus ainsi que dans le
rapport d'architecture et docs/161-architecture-agent-recherche.md — pas
appliqués silencieusement.
