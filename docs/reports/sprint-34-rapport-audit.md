# Rapport d'audit — Sprint 34 (Agent Jurisprudence, réel)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« PHASE 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), ce qui
existe déjà pour chacun des fichiers désignés par le prompt, et confirme
qu'aucun n'a changé de forme depuis son sprint d'origine.

## Fichiers désignés par le prompt : forme confirmée, aucun écart de contenu

| Fichier | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `tmis.agents.jurisprudence_agent.JurisprudenceAgent` | Placeholder Sprint 1 : `name = "jurisprudence"`, `async def run(agent_input) -> AgentOutput: raise NotImplementedError(...)` | Confirmé exact — remplacé par ce sprint |
| `tmis.agents.orchestrator.Orchestrator` | Graphe LangGraph `analysis -> verifier -> synthesis -> verifier_final -> END` ; docstring documentant le patron pour un agent futur — **ni `ResearchAgent` (Sprint 33) ni aucun autre agent au-delà de `analysis`/`verifier`/`synthesis` n'est câblé sur ce graphe** | Confirmé exact — **non modifié** ; ce sprint ne demande pas de nœud `"jurisprudence"`, et `ResearchAgent` lui-même (patron de référence explicite du prompt) n'y a jamais été ajouté au Sprint 33 |
| `tmis.agents.contracts` | Ré-export de `AgentInput`/`AgentOutput`/`AgentPort`/`ConfidenceLevel` depuis `tmis.ai.schemas.agent` | Confirmé exact, aucune modification |
| `tmis.agents.bootstrap` | `get_research_agent()` : `@lru_cache`, compose `get_research_orchestrator()` + `get_ai_governance_platform()` | Confirmé exact — patron de composition-root réutilisé pour `get_jurisprudence_agent()` |
| `tmis.agents.research_agent.ResearchAgent` (patron de référence Sprint 33) | Délégation complète à `ResearchOrchestrator.search(raw_text, case_id=...)`, adaptateur `Citation` explicite (`_to_citation`, méthode statique privée), aucun câblage `AIIntelligenceFabric`/`TMISKernel` | Confirmé exact — patron de recherche/citations réutilisé ; `_to_citation` extrait en fonction partagée (voir écart n°1 ci-dessous) |
| `tmis.agents.analysis_agent.AnalysisAgent` (patron de référence Sprint 29) | Constructeur `kernel`/`document_store`/`case_store`/`fabric`/`governance`/`firm_id`, tous optionnels ; `AIIntelligenceFabric.route(RoutingRequest(firm_id, task_type, prompt))` pour choisir le modèle d'un appel `TMISKernel.complete(prompt, provider=...)` ; `AIGovernancePlatform.explainability.generate()` optionnel | Confirmé exact — patron de câblage Fabric/Kernel/Governance réutilisé pour la comparaison générative |
| `tmis.legal_research.search.orchestrator.ResearchOrchestrator` | `search(raw_text, *, filters=None, connector_names: list[str] \| None = None, weights=None, user_id=None, case_id=None) -> ResearchResponse` — `connector_names` déjà accepté et déjà transmis à `HybridResearchSearch.execute(query, connector_names=connector_names)` à travers toute la chaîne de cache (`_resolve_raw`/`_resolve_normalized`/`_resolve_ranked_results`) | **Confirmé exact — découverte clé validée** : aucune signature à changer, `connector_names=["jurisprudence"]` suffit à filtrer la recherche sur le seul connecteur jurisprudence |
| `tmis.legal_research.bootstrap.get_research_orchestrator` | `@lru_cache`, `kernel = get_kernel()` ; `register_legal_research_connectors(kernel.connector_manager, internal_documentation=..., private_database=...)` — **n'enregistre que ces deux connecteurs LRE-spécifiques**, pas `"jurisprudence"` | Confirmé exact — le connecteur `"jurisprudence"` est déjà présent sur `kernel.connector_manager` **avant** cet appel (voir ligne suivante), `register_legal_research_connectors` n'a pas besoin de le faire une seconde fois |
| `tmis.ai.kernel.bootstrap.get_kernel` | `connector_manager = ConnectorManager(codes=build_codes_connector(), jurisprudence=build_jurisprudence_connector(), doctrine=build_doctrine_connector())` | **Confirmé exact — écart de découverte du prompt validé** : `"jurisprudence"` est bien une clé du `ConnectorManager` partagé du Kernel, construite au Sprint 27, indépendamment du LRE |
| `tmis.ai.connectors.manager.ConnectorManager` | `__init__(*, codes=None, jurisprudence=None, doctrine=None)` stocke sous les clés littérales `"codes"`/`"jurisprudence"`/`"doctrine"` ; `search(query, *, connector_names=None)` filtre `targets = connector_names or list(self._entries)` | Confirmé exact — la clé `"jurisprudence"` passée à `ResearchOrchestrator.search(connector_names=["jurisprudence"])` correspond exactement à cette entrée |
| `tmis.ai.connectors.factory.build_jurisprudence_connector` | Retourne `JudilibreConnector` (réel, si `TMIS_PISTE_CLIENT_ID`/`_SECRET` configurés) sinon `JurisprudenceConnector` (fixture Sprint 2) | Confirmé exact — les deux implémentent le même `ConnectorPort`, interchangeables du point de vue de `JurisprudenceAgent` |
| `tmis.ai.schemas.citation.Citation` | `frozen`/`slots` : `source_id`, `connector`, `excerpt`, `reference` — aucun champ `title`/`date` ; `RetrievedChunk.to_citation(connector, reference)` confirme que `connector` est toujours fourni explicitement | Confirmé exact, aucune modification |
| `tmis.legal_research.citations.schemas.ResearchCitation` | `frozen`/`slots` : `source_id`, `title`, `date`, `document_type`, `reference`, `excerpt` — aucun champ `connector` | Confirmé exact, aucune modification |
| `tmis.ai_fabric.fabric.AIIntelligenceFabric` | `route(RoutingRequest) -> RoutingDecision` — `RoutingDecision.model` porte `name` et `provider` | Confirmé exact, aucune modification |
| `tmis.ai.kernel.kernel.TMISKernel.complete` | `complete(prompt, *, provider=None, use_cache=True) -> ModelResponse` — seul point d'appel à un provider (`self.provider_registry.get(provider_name)`) | Confirmé exact, aucune modification |
| `tmis.ai_governance.overview.AIGovernancePlatform` | `explainability.generate(firm_id, production_id, *, summary, steps_followed, agents_involved=(), models_used=(), documents_consulted=())` | Confirmé exact, aucune modification |
| `tmis.case_intelligence.cases.ports.CaseStorePort` / `.schemas.CaseProfile` | `CaseStorePort.get(case_id: str) -> CaseProfile \| None` ; `CaseProfile.title`/`.actors`/`.facts` | Confirmé exact — utilisé pour injecter le dossier dans la comparaison, même patron que `AnalysisAgent` |

Aucun de ces fichiers n'avait un contenu différent de celui attendu — le
seul travail de Phase 0 a été de confirmer, par lecture directe, que la
« découverte clé » annoncée par le prompt (le connecteur `"jurisprudence"`
est déjà cherchable via le LRE) est exacte, et de trancher un écart
structurel hérité du Sprint 33.

## Découverte clé confirmée : `"jurisprudence"` est un connecteur du Kernel, pas du LRE

Le prompt affirme que le connecteur jurisprudence est « déjà enregistré
sur le `ConnectorManager` partagé du Kernel et donc déjà cherchable par
le LRE ». La lecture directe de la chaîne complète le confirme :

1. `tmis.ai.kernel.bootstrap.get_kernel()` construit
   `ConnectorManager(codes=..., jurisprudence=build_jurisprudence_
   connector(), doctrine=...)` — la clé `"jurisprudence"` existe dès la
   construction du Kernel, indépendamment de tout module `legal_research`.
2. `tmis.legal_research.bootstrap.get_research_orchestrator()` réutilise
   ce même `kernel.connector_manager` (`kernel = get_kernel()`) pour
   construire `HybridResearchSearch(kernel, default_connectors=kernel.
   connector_manager.list_connectors())` — `list_connectors()` inclut donc
   `"jurisprudence"` dans la liste par défaut.
3. `ResearchOrchestrator.search(..., connector_names=["jurisprudence"])`
   transmet ce filtre à `HybridResearchSearch.execute(query,
   connector_names=connector_names)`, qui le relaie jusqu'à
   `ConnectorManager.search(query, connector_names=connector_names)` —
   dont le code (`targets = connector_names or list(self._entries)`)
   restreint alors la recherche à la seule entrée `"jurisprudence"`.

**Conclusion** : `JurisprudenceAgent` n'a besoin d'ajouter aucun
connecteur, aucun moteur, aucun paramètre à `ResearchOrchestrator.
search()` — le filtre existe déjà dans la signature publique.

## Écart structurel confirmé, tranché avant tout code

### `ResearchCitation` ne porte pas de nom de connecteur — même écart qu'au Sprint 33, adaptateur réutilisé à l'identique

Identique à l'écart n°2 du Sprint 33 (`docs/reports/sprint-33-rapport-
audit.md`) : `ResearchCitation` ne porte pas de champ `connector`,
`Citation` en exige un. La Phase 0 confirme que
`ResearchOrchestrator.search()` garantit toujours l'alignement
positionnel entre `response.results` et `get_citations(search_id)` (même
liste `ranked`, même ordre, même méthode — non modifié depuis le Sprint
33).

**Décision** : plutôt que de recopier `ResearchAgent._to_citation` telle
quelle dans `JurisprudenceAgent` (un second chemin de conversion textuel
identique, interdit explicitement par le prompt), la fonction est extraite
de `research_agent.py` vers un module partagé
`tmis.agents.citations.research_citation_to_citation`, et `ResearchAgent`
est mis à jour pour l'appeler au lieu de sa propre méthode statique. Les
deux agents appellent donc littéralement la même fonction — vérifié par
`grep -rn "research_citation_to_citation" tmis/agents/` qui ne montre
qu'un seul point de définition et deux points d'appel.

## Confirmation explicite : aucun autre agent, aucune modification du LRE ni des plateformes partagées

- `ContractAgent`, `WatchAgent`, `DraftingAgent`, `StrategyAgent`,
  `CollaborationAgent` : **aucune ligne modifiée**.
- `tmis.agents.orchestrator.Orchestrator` : **non modifié** — ni le
  graphe LangGraph, ni sa signature publique `run()`.
- `tmis.legal_research.search.orchestrator.ResearchOrchestrator` et tout
  son pipeline interne : **aucune ligne modifiée** — vérifié par `git diff
  --stat` restreint à `tmis/legal_research/`, vide.
- `tmis.ai.kernel.kernel.TMISKernel`, `tmis.ai_fabric.fabric.
  AIIntelligenceFabric`, `tmis.ai_governance.overview.
  AIGovernancePlatform` : **aucune ligne modifiée**.
- `tmis.legal_research.citations.schemas.ResearchCitation` et
  `tmis.ai.schemas.citation.Citation` : **zéro changement de signature**.
- Mode `"research"` du chat (Sprint 33) : **non étendu** à la
  jurisprudence — confirmé non trivial (voir
  docs/162-architecture-agent-jurisprudence.md, section « Ce qui reste
  volontairement hors périmètre »), documenté comme scope futur plutôt
  qu'improvisé.

## Conclusion

Aucun des fichiers désignés par le prompt n'avait un contenu différent de
celui attendu. La découverte clé annoncée par le prompt (connecteur
`"jurisprudence"` déjà partagé par le Kernel et donc déjà cherchable via
`ResearchOrchestrator.search(connector_names=["jurisprudence"])`) est
confirmée exacte par lecture directe de la chaîne complète
Kernel → LRE → `HybridResearchSearch` → `ConnectorManager`. Un seul écart
structurel a été identifié, hérité à l'identique du Sprint 33
(`ResearchCitation` sans champ `connector`) et tranché par extraction de
l'adaptateur existant en fonction partagée plutôt que par une nouvelle
implémentation — documenté ici ainsi que dans le rapport d'architecture
et docs/162-architecture-agent-jurisprudence.md, pas appliqué
silencieusement.
