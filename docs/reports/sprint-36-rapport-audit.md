# Rapport d'audit — Sprint 36 (Agent Veille, réel)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« PHASE 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), ce qui
existe déjà pour chacun des fichiers désignés par le prompt, confirme
qu'aucun n'a changé de forme depuis son sprint d'origine, et tranche les
deux questions ouvertes explicitement posées par la mission.

## Fichiers désignés par le prompt : forme confirmée, aucun écart de contenu

| Fichier | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `tmis.agents.watch_agent.WatchAgent` | Placeholder Sprint 1 : `name = "watch"`, `async def run(agent_input) -> AgentOutput: raise NotImplementedError(...)` | Confirmé exact — remplacé par ce sprint |
| `tmis.agents.orchestrator.Orchestrator` | Graphe LangGraph `analysis -> verifier -> synthesis -> verifier_final -> END` ; docstring documentant le patron pour un agent futur — aucun agent au-delà de `analysis`/`verifier`/`synthesis` n'y est câblé | Confirmé exact — **non modifié** ; ce sprint ne demande pas de nœud `"watch"`, et ni `ResearchAgent`, ni `JurisprudenceAgent`, ni `ContractAgent` n'y ont jamais été ajoutés (même précédent que les Sprints 34/35) |
| `tmis.agents.contracts` | Ré-export de `AgentInput`/`AgentOutput`/`AgentPort`/`ConfidenceLevel` depuis `tmis.ai.schemas.agent` | Confirmé exact, aucune modification |
| `tmis.agents.bootstrap` | `get_research_agent()`, `get_jurisprudence_agent()`, `get_contract_agent()` : `@lru_cache`, composition-root | Confirmé exact — patron réutilisé pour `get_watch_agent()` |
| `tmis.agents.citations` | `research_citation_to_citation(result, citation) -> Citation`, utilisé par `ResearchAgent`/`JurisprudenceAgent` | Confirmé exact — réutilisé tel quel par `WatchAgent`, aucun second chemin de conversion |
| `tmis.agents.research_agent.ResearchAgent` (patron de référence recherche filtrée par connecteurs) | Délégation pure à `ResearchOrchestrator.search(raw_text, case_id=...)`, sans `AIIntelligenceFabric` (aucun travail génératif propre à cet agent) | Confirmé exact — patron réutilisé pour la partie recherche de `WatchAgent`, avec `connector_names` en plus (configurable, pas fixé en dur) |
| `tmis.agents.jurisprudence_agent.JurisprudenceAgent` / `tmis.agents.contract_agent.ContractAgent` (patrons de référence recherche + synthèse générative) | Combinent délégation à un port existant (recherche/lecture) et câblage `AIIntelligenceFabric.route()` → `TMISKernel.complete()` sur le même agent, tous deux avec `governance` optionnel | Confirmés exacts — précédent direct pour combiner recherche filtrée par connecteurs et synthèse générative optionnelle sur `WatchAgent` |
| `tmis.legal_research.search.orchestrator.ResearchOrchestrator.search` | `search(raw_text, *, filters=None, connector_names=None, weights=None, user_id=None, case_id=None) -> ResearchResponse` ; enregistre l'historique et les métriques à chaque appel ; `get_citations(search_id)` retourne les `ResearchCitation` dans le même ordre que `response.results` | Confirmé exact, signature inchangée, aucune modification |
| `tmis.ai.connectors.manager.ConnectorManager.list_connectors` | `list_connectors() -> list[str]`, retourne les noms déjà enregistrés (`codes`, `jurisprudence`, `doctrine` par défaut, plus tout connecteur ajouté via `register()`) ; `search(connector_names=...)` ignore silencieusement un nom inconnu ou désactivé | Confirmé exact — **DÉCOUVERTE CLÉE validée** : les « sources configurées » de la mission ne sont pas un nouveau registre, seulement une liste de `connector_names` parmi ceux déjà connus, passée telle quelle à `ResearchOrchestrator.search()` |
| `tmis.legal_research.history.ports.ResearchHistoryPort` | `record(entry)`, `list_for_user`, `list_for_case`, `list_all` — aucune méthode de comparaison entre deux exécutions | Confirmé exact — **confirmé insuffisant pour la détection de nouveauté**, voir Question Ouverte n°1 |
| `tmis.legal_research.history.schemas.ResearchHistoryEntry` | `id`, `query_text`, `timestamp`, `connectors_used`, `duration_ms`, `result_count`, `user_id`, `case_id` — pas de liste d'identifiants de résultats | Confirmé exact — même constat : `result_count` est un entier, pas un ensemble d'identifiants comparable d'une exécution à l'autre |
| `tmis.legal_research.history.in_memory_history.InMemoryResearchHistory` | Implémentation `ResearchHistoryPort` par liste en mémoire | Confirmé exact, aucune modification |
| `tmis.domain.watch.__init__` | Paquet vide, docstring : « Implementation scheduled in a future sprint » | Confirmé exact — **vestige vide, comme `domain.case_analysis` tranché au Sprint 29** ; non peuplé par ce sprint, `WatchAgent` n'en importe rien |
| `tmis.core.tasks.{celery_app,document_tasks,case_tasks}` | Un `Celery` unique (`tmis.core.tasks.celery_app`), déclenché exclusivement de façon **événementielle** (upload -> pipeline DIE -> CIE) ; aucun `beat_schedule`, aucune tâche planifiée dans tout le dépôt | Confirmé exact — **non câblé pour ce sprint**, voir Question Ouverte n°2 |
| `tmis.ai_fabric.fabric.AIIntelligenceFabric` | `route(RoutingRequest) -> RoutingDecision` — `RoutingDecision.model` porte `name` et `provider` | Confirmé exact, aucune modification |
| `tmis.ai.kernel.kernel.TMISKernel.complete` | `complete(prompt, *, provider=None, use_cache=True) -> ModelResponse` — seul point d'appel à un provider | Confirmé exact, aucune modification |
| `tmis.ai_governance.overview.AIGovernancePlatform` | `explainability.generate(firm_id, production_id, *, summary, steps_followed, agents_involved=(), models_used=(), documents_consulted=())` | Confirmé exact, aucune modification |

Aucun de ces fichiers n'avait un contenu différent de celui attendu.
Deux questions structurantes, explicitement posées par la mission, ont
été tranchées avant tout code — plus une troisième, soulevée par la
mission elle-même sous une forme moins formelle (« évaluer... »),
également documentée.

## Question Ouverte n°1 (posée par le prompt) : détection de nouveauté — stateless ou nouveau store ?

**Option (a), stateless.** La lecture directe de
`tmis.legal_research.history.{ports,schemas,in_memory_history}` confirme
que `ResearchHistoryPort` journalise chaque recherche
(`ResearchHistoryEntry`) mais ne conserve même pas la liste des
`ResearchResult.id` d'une exécution (seulement `result_count: int`) et
n'expose aucune méthode de comparaison entre deux entrées. Ce n'est
structurellement pas un mécanisme de détection de nouveauté ; l'étendre à
cet usage aurait exigé de lui faire porter un rôle qu'il n'a jamais eu
vocation à couvrir.

**Décision** : `WatchAgent` reste intégralement stateless. L'appelant
fournit `agent_input.context["known_result_ids"]` (identifiants déjà
connus d'une exécution précédente de la même veille) ; l'agent renvoie
comme `new_results` uniquement les résultats dont l'identifiant n'y
figure pas, et renvoie systématiquement l'ensemble des identifiants de
cette exécution (`result_ids`) pour que l'appelant les fusionne (union)
avant la prochaine exécution. Aucun `WatchStorePort` n'est introduit —
voir docs/164-architecture-agent-veille.md pour le détail complet du
raisonnement, notamment pourquoi (b) n'est pas nécessaire : le contrat
`AgentPort` est déjà stateless pour les six autres agents de
`tmis.agents`, et conserver un ensemble d'identifiants d'un appel à
l'autre est trivial côté appelant.

## Question Ouverte n°2 (posée par le prompt) : câblage d'une tâche Celery périodique ?

**Non.** La mission ne mentionne, pour ce sprint, que « alertes ciblées
depuis sources configurées » — pas de planification automatique. La
lecture directe de `tmis.core.tasks.{celery_app,document_tasks,
case_tasks}` confirme que le patron Celery existant ne déclenche
aujourd'hui que des traitements **événementiels** (upload d'un document
-> pipeline DIE -> CIE) ; aucune tâche du dépôt ne s'exécute sur un
`crontab`/`beat_schedule`, et `celery_app.conf` ne configure aucun
`beat_schedule`.

**Décision** : aucune tâche Celery périodique ajoutée. `WatchAgent.run()`
s'exécute exclusivement à la demande, comme les six autres agents.
Câbler une veille récurrente exigerait un `beat_schedule` (absent du
dépôt), une configuration de veille nommée et persistée (hors périmètre
de la Question Ouverte n°1) et un mécanisme de notification (absent) —
ni triviale, ni strictement additive au patron Celery existant. Ce sujet
reste un sprint futur, non couvert par cette table de 41 sprints.

## Question soulevée par la mission (« évaluer en Phase 0 ») : l'alerte doit-elle rester structurée/déterministe ou devenir narrative/générative ?

**Les deux, sans se substituer l'une à l'autre.** Le contenu structuré
(`new_results`, un par résultat nouveau, avec `id`/`title`/`excerpt`/
`connector`/`reference`/`date`/`score`) reste systématiquement la source
de vérité de l'alerte — jamais dépendant d'une génération pour être
correct. Un message narratif optionnel (`alert_message`), produit via
`AIIntelligenceFabric.route()` → `TMISKernel.complete()` (même patron que
les trois agents précédents, un seul point d'appel génératif), n'est
généré que s'il existe au moins un résultat nouveau — voir
docs/164-architecture-agent-veille.md pour le raisonnement complet.

## Confirmation explicite : aucun autre agent, aucune modification des ports ni des plateformes partagées

- `ResearchAgent`, `JurisprudenceAgent`, `ContractAgent` : **aucune ligne
  modifiée** — ce sprint ne touche à aucun autre agent déjà réel.
- `DraftingAgent`, `StrategyAgent`, `CollaborationAgent` : **aucune ligne
  modifiée**.
- `tmis.agents.orchestrator.Orchestrator` : **non modifié** — ni le
  graphe LangGraph, ni sa signature publique `run()`.
- `tmis.legal_research.search.orchestrator.ResearchOrchestrator`,
  `tmis.ai.connectors.manager.ConnectorManager` : **aucune ligne
  modifiée** — vérifié par `git diff --stat` restreint à
  `tmis/legal_research/` et `tmis/ai/connectors/`, vide.
- `tmis.legal_research.history.*` (`ResearchHistoryPort` et son
  implémentation in-memory) : **aucune ligne modifiée** — lu, confirmé
  insuffisant pour la détection de nouveauté, jamais étendu ni fusionné
  avec un nouveau store.
- `tmis.domain.watch` : **aucune ligne modifiée** — vestige vide confirmé,
  non peuplé.
- `tmis.core.tasks.*` : **aucune ligne modifiée** — aucune tâche Celery
  périodique ajoutée (voir Question Ouverte n°2).
- `tmis.ai.kernel.kernel.TMISKernel`, `tmis.ai_fabric.fabric.
  AIIntelligenceFabric`, `tmis.ai_governance.overview.
  AIGovernancePlatform` : **aucune ligne modifiée**.
- `AgentInput`/`AgentOutput`/`AgentPort`/`ResearchOrchestrator.search()`/
  `Citation`/`ResearchCitation` : **zéro changement de signature**.

## Composants réutilisés tels quels / étendus / réellement nouveaux

| Composant | Statut | Détail |
|---|---|---|
| `ResearchOrchestrator.search(connector_names=...)` (Sprint 5) | Réutilisé tel quel | Seul moteur de recherche, `connector_names` désormais fourni par une configuration de veille plutôt que fixé en dur (comme `JurisprudenceAgent`) ou omis (comme `ResearchAgent`) |
| `ConnectorManager` (Sprint 5) | Réutilisé tel quel | `list_connectors()` confirme qu'aucun nouveau registre n'est nécessaire |
| `tmis.agents.citations.research_citation_to_citation` (Sprint 33) | Réutilisé tel quel | Même adaptateur que `ResearchAgent`/`JurisprudenceAgent`, aucun second chemin de conversion |
| `AIIntelligenceFabric.route()` (Sprint 14) | Réutilisé tel quel | `task_type="watch_alert_synthesis"`, nouveau uniquement comme valeur de chaîne libre |
| `TMISKernel.complete()` (Sprint 2) | Réutilisé tel quel | Seul point d'appel génératif, appelé uniquement s'il existe au moins un résultat nouveau |
| `AIGovernancePlatform.explainability` (Sprint 15) | Réutilisé tel quel | Même patron `generate()` que les trois agents précédents |
| `tmis.agents.bootstrap` (composition root) | Étendu | Ajout de `get_watch_agent()`, aucune fonction existante modifiée |
| `WatchAgent._resolve_connectors`/`_resolve_known_ids` | Réellement nouveau | Lecture de la configuration de veille (`connectors`, `known_result_ids`) depuis `agent_input.context` |
| `WatchAgent` — filtrage stateless des résultats nouveaux | Réellement nouveau | Absent ailleurs dans le dépôt : aucun autre composant ne compare le contenu de deux recherches entre elles |
| `WatchAgent._generate_alert`/`_build_prompt` | Réellement nouveau | Synthèse narrative d'alerte, absente ailleurs |
| `ResearchHistoryPort` | Non retenu pour la détection de nouveauté (évalué, écarté) | Journalise mais ne compare jamais deux exécutions — voir Question Ouverte n°1 |
| `WatchStorePort` (option 1b) | Non retenu | Option (a) stateless jugée suffisante — voir Question Ouverte n°1 |
| Tâche Celery périodique | Non retenue | Aucune planification automatique dans le périmètre de ce sprint — voir Question Ouverte n°2 |

## Conclusion

Aucun des fichiers désignés par le prompt n'avait un contenu différent de
celui attendu. Les trois questions structurantes de ce sprint —
détection de nouveauté, planification Celery, et nature de l'alerte
(structurée ou générative) — ont toutes été tranchées avant tout code et
documentées ici, dans le rapport d'architecture et
docs/164-architecture-agent-veille.md, jamais appliquées silencieusement.
Avec ce sprint, les sept agents réels de `tmis.agents` prévus par ce
roadmap de 41 sprints (`AnalysisAgent`, `SynthesisAgent`, `VerifierAgent`,
`ResearchAgent`, `JurisprudenceAgent`, `ContractAgent`, `WatchAgent`) sont
tous livrés ; `DraftingAgent`/`StrategyAgent`/`CollaborationAgent`
restent, eux, hors de ce roadmap.
