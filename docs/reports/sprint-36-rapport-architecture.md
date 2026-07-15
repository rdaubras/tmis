# Rapport d'architecture — Sprint 36 (Agent Veille, réel)

## Résumé

Le Sprint 36 relie `WatchAgent` (placeholder depuis le Sprint 1) aux
plateformes déjà livrées, en combinant les deux patrons établis par les
sprints précédents : délégation pure à un port existant pour la
recherche (`ResearchAgent`, Sprint 33) et câblage
`AIIntelligenceFabric.route()` → `TMISKernel.complete()` pour une
synthèse générative optionnelle (`JurisprudenceAgent`/`ContractAgent`,
Sprints 34/35). Le travail réellement nouveau — confirmé absent ailleurs
dans le dépôt par la Phase 0
(`docs/reports/sprint-36-rapport-audit.md`) — est la structure d'une
« configuration de veille » (`query` + `connectors` surveillés +
`case_id` optionnel), le filtrage stateless de ce qui est nouveau depuis
la dernière exécution, et une synthèse d'alerte qui reste toujours
secondaire au contenu structuré qu'elle résume.

Périmètre livré : `tmis/agents/watch_agent.py` (réécrit, placeholder ->
implémentation réelle), `tmis/agents/bootstrap.py` (ajout de
`get_watch_agent()`), 16 tests unitaires + 4 tests d'intégration
nouveaux, 0 test existant modifié, docs/164-architecture-agent-veille.md,
note de révision dans docs/09-roadmap-30-sprints.md.

**Aucun autre agent de `tmis.agents` touché. `ResearchOrchestrator`,
`ConnectorManager`, `ResearchHistoryPort`, `AIIntelligenceFabric`,
`TMISKernel`, `AIGovernancePlatform` non modifiés. `Orchestrator`
(LangGraph) non modifié. Aucune tâche Celery périodique ajoutée. Zéro
changement de signature sur `AgentInput`/`AgentOutput`/`AgentPort`/
`ResearchOrchestrator.search()`/`Citation`/`ResearchCitation`.**

## Décisions structurantes

### La configuration de veille traduit `connectors` en `connector_names`, sans second registre

`ConnectorManager.list_connectors()` (`tmis.ai.connectors.manager`)
confirme que les connecteurs sont déjà tous enregistrés sur le
`ConnectorManager` partagé du Kernel — « sources configurées » de la
mission n'introduit donc aucun nouveau registre :

```python
connector_names = self._resolve_connectors(agent_input.context.get("connectors"))
case_id = str(agent_input.case_id) if agent_input.case_id is not None else None
response = await self._orchestrator.search(
    query, connector_names=connector_names, case_id=case_id
)
```

Contrairement à `JurisprudenceAgent`, qui fixe en dur
`_JURISPRUDENCE_CONNECTORS = ["jurisprudence"]`, `WatchAgent` laisse
l'appelant choisir les connecteurs à surveiller (`context["connectors"]`,
`None` par défaut recherchant tous les connecteurs — même comportement
que `ResearchAgent` dans ce cas). Un nom de connecteur inconnu ou
désactivé n'a besoin d'aucune validation supplémentaire côté
`WatchAgent` : `ConnectorManager.search()` l'ignore déjà silencieusement.
Vérifié par test (`test_watch_agent_filters_search_on_configured_
connectors`, `test_watch_agent_searches_all_connectors_when_none_
configured`).

### Détection de nouveauté : Question Ouverte n°1 — stateless, `ResearchHistoryPort` confirmé insuffisant

La mission posait explicitement la question et exigeait qu'elle soit
tranchée en Phase 0. Lecture directe de `tmis.legal_research.history.
{ports,schemas,in_memory_history}` : `ResearchHistoryPort.record()`
journalise une `ResearchHistoryEntry` par recherche mais ne conserve même
pas la liste des `ResearchResult.id` de cette recherche (seulement
`result_count: int`), et aucune méthode n'existe pour comparer deux
entrées entre elles. Ce n'est donc structurellement pas un mécanisme de
détection de nouveauté.

**Décision** : `WatchAgent` reste intégralement stateless (option a) :

```python
known_result_ids = self._resolve_known_ids(agent_input.context.get("known_result_ids"))
...
new_pairs: list[_ResultCitationPair] = [
    (result, citation)
    for result, citation in zip(response.results, research_citations, strict=True)
    if result.id not in known_result_ids
]
```

`result["result_ids"]` renvoie systématiquement l'ensemble des
identifiants de cette exécution (pas seulement les nouveaux), pour que
l'appelant les fusionne (union, jamais remplacement) avec son propre
`known_result_ids` avant la prochaine exécution de la même veille. Aucun
`WatchStorePort` (option b) n'est introduit : le contrat `AgentPort` est
déjà stateless pour les six autres agents de `tmis.agents`, et conserver
un ensemble d'identifiants d'un appel à l'autre est trivial côté
appelant — qui a de toute façon besoin d'un mécanisme de planification/
persistance de configuration que ce sprint n'implémente pas (voir
Question Ouverte n°2). Vérifié par test
(`test_watch_agent_returns_no_new_result_when_everything_is_already_known`,
`test_watch_agent_only_reports_results_absent_from_known_ids`,
`test_a_second_run_with_the_first_runs_ids_reports_no_new_result`).

### Aucune tâche Celery périodique : Question Ouverte n°2 tranchée avant tout code

La mission ne mentionne, pour ce sprint, que « alertes ciblées depuis
sources configurées » — pas de planification automatique. Lecture
directe de `tmis.core.tasks.{celery_app,document_tasks,case_tasks}` :
le patron Celery existant ne déclenche que des traitements
**événementiels** (upload -> pipeline DIE -> CIE), jamais périodiques ;
`celery_app.conf` ne configure aucun `beat_schedule`.

**Décision** : aucune tâche Celery périodique ajoutée. `WatchAgent.run()`
s'exécute exclusivement à la demande, comme les six autres agents.
Câbler une veille récurrente exigerait un `beat_schedule` (absent du
dépôt), une configuration de veille nommée et persistée (hors périmètre
de la Question Ouverte n°1) et un mécanisme de notification (absent) —
ni triviale, ni strictement additive. Ce sujet reste un sprint futur non
couvert par cette table de 41 sprints.

### La synthèse d'alerte est générative mais jamais le seul support des faits

La mission demandait d'évaluer si une alerte gagne à rester
structurée/déterministe plutôt que narrative. Décision : les deux,
sans exclusivité. `new_results` (structuré, calculé sans passer par un
modèle) reste systématiquement présent et **est** la source de vérité de
l'alerte. Un message narratif optionnel, `alert_message`, est généré
par-dessus, seulement s'il existe au moins un résultat nouveau :

```python
async def _generate_alert(
    self, query: str, new_pairs: list[_ResultCitationPair], case_id: str | None
) -> tuple[str, str]:
    prompt = self._build_prompt(query, new_pairs, case_id)
    model_name, provider_name = self._route_model(prompt)
    completion = await self._kernel.complete(prompt, provider=provider_name)
    return model_name, completion.text
```

`_route_model()` reproduit exactement le patron des trois agents
précédents : `RoutingRequest(firm_id, "watch_alert_synthesis", prompt)`
(un `task_type` propre à ce sprint), retombant sur `"default", None`
sans `fabric` injecté. Contrairement à une alerte qui reposerait
exclusivement sur un texte généré (risque de paraphrase inexacte d'une
référence, d'une date ou d'un extrait), le contenu structuré reste
consultable indépendamment de toute génération — cohérent avec le fait
qu'une veille est fondamentalement un filtrage, pas un jugement nouveau
comme la comparaison de jurisprudence ou la synthèse de risques
contractuels. Vérifié par test
(`test_watch_agent_generates_an_alert_without_a_fabric`,
`test_watch_agent_routes_alert_through_the_fabric`,
`test_watch_agent_records_explainability_without_generation_when_
nothing_new`).

### Confiance

```python
@staticmethod
def _confidence_for(response: ResearchResponse) -> ConfidenceLevel:
    if not response.results:
        return ConfidenceLevel.LOW
    if response.cache_hit:
        return ConfidenceLevel.HIGH
    return ConfidenceLevel.MEDIUM
```

Même structure que `ResearchAgent._confidence_for` : la confiance
reflète la fiabilité de la recherche elle-même, pas le nombre de
résultats *nouveaux* — une veille qui ne trouve rien de nouveau depuis
la dernière exécution reste une recherche réussie (avertissement
explicite, pas de dégradation de confiance).

### Explicabilité

`AIGovernancePlatform.explainability.generate(...)` enregistre, pour
chaque exécution : la requête et les connecteurs surveillés, le nombre de
résultats reçus et le nombre de résultats nouveaux, et le modèle utilisé
pour l'alerte si une génération a eu lieu — optionnel comme pour les
trois agents précédents. `documents_consulted` ne référence que les
résultats nouveaux, pas l'ensemble des résultats de la recherche.

### `WatchAgent` n'est câblé ni dans l'`Orchestrator` ni dans le chat, ni sur une tâche Celery

Même choix que `ResearchAgent`/`JurisprudenceAgent`/`ContractAgent` avant
lui pour les deux premiers points (aucun des trois n'a jamais été ajouté
au graphe LangGraph ni exposé dans un mode dédié du chat) ; l'absence de
câblage Celery est, elle, une décision explicite de ce sprint (Question
Ouverte n°2), pas un oubli.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `WatchAgent` (recherche) | `ResearchOrchestrator.search(connector_names=...)` (Sprint 5, inchangé) | Un second moteur de recherche, un second registre de connecteurs |
| `WatchAgent` (citations) | `tmis.agents.citations.research_citation_to_citation` (Sprint 33, inchangé) | Un second chemin de conversion de citations |
| `WatchAgent._resolve_known_ids` / filtrage `new_pairs` | `agent_input.context["known_result_ids"]` (fourni par l'appelant) | Un `WatchStorePort`, un second `ResearchHistoryPort` |
| `WatchAgent._generate_alert` | `AIIntelligenceFabric.route()` (Sprint 14), `TMISKernel.complete()` (Sprint 2) | Un second client LLM, un second routeur de modèle |
| `WatchAgent._record_explainability` | `AIGovernancePlatform.explainability.generate()` (Sprint 15) | Une gouvernance de production parallèle |
| `tmis.agents.bootstrap.get_watch_agent` | `get_research_orchestrator()` (Sprint 5), `get_kernel()` (Sprint 2), `get_ai_intelligence_fabric()` (Sprint 14), `get_ai_governance_platform()` (Sprint 15) — même patron `@lru_cache` que `get_jurisprudence_agent()`/`get_contract_agent()` | Un second singleton d'orchestrateur, de Kernel, de Fabric ou de plateforme de gouvernance |

## Aucun test existant modifié

`WatchAgent` était un placeholder qui levait `NotImplementedError` —
aucun test préexistant ne l'exerçait au-delà de vérifier cette exception.
`git diff --stat` sur `tests/` en dehors des deux nouveaux fichiers est
vide.

20 tests nouveaux :

- `tests/unit/agents/test_watch_agent.py` (+16, nouveau fichier) :
  absence de query -> `LOW`, aucun résultat -> `LOW`, recherche filtrée
  sur les connecteurs configurés, recherche non filtrée quand aucun
  connecteur n'est configuré, conversion des citations sur un vrai
  `ResearchOrchestrator` de test, aucun résultat nouveau quand tous les
  identifiants sont déjà connus (avec avertissement explicite et
  `result_ids` toujours renseigné), filtrage correct d'un sous-ensemble
  de résultats déjà connus, synthèse générée sans/avec `fabric` injecté,
  transmission du `case_id` à l'historique de l'orchestrateur,
  explicabilité enregistrée avec et sans génération.
- `tests/integration/agents/test_watch_agent_integration.py` (+4,
  nouveau fichier) : bout en bout sur un vrai `ResearchOrchestrator`
  (première exécution -> tout est nouveau, alerte générée), une seconde
  exécution avec les identifiants de la première ne rapporte plus rien de
  nouveau, transmission du `case_id` à l'historique, absence de query.

## Vérification finale

- `pytest -q` (depuis `backend/`) → **2183 passed, 7 skipped** (2167
  tests préexistants + 16 nouveaux, 0 régression ; les 7 `skipped` sont
  préexistants, gatés par `TMIS_REDIS_URL`/
  `TMIS_RUN_MODEL_DOWNLOAD_TESTS`, non liés à ce sprint).
- `ruff check src tests` (commande CI) → **All checks passed**.
- `mypy src` (commande CI, mode strict) → **Success: no issues found in
  1896 source files**.
- Confirmation explicite de périmètre : `git diff --stat` sur
  `tmis/agents/` ne montre que `watch_agent.py` (réécrit) et
  `bootstrap.py` (ajout de `get_watch_agent()`). `git diff --stat` sur
  `tmis/legal_research/`, `tmis/ai/connectors/`, `tmis/domain/watch/`,
  `tmis/core/tasks/`, `tmis/agents/orchestrator.py`, `tmis/ai_fabric/`,
  `tmis/ai/kernel/`, `tmis/ai_governance/` est vide.

## Dernier agent de `tmis.agents` prévu par ce roadmap

Avec ce sprint, les sept agents réels prévus par cette table de 41
sprints (`AnalysisAgent`, `SynthesisAgent`, `VerifierAgent`,
`ResearchAgent`, `JurisprudenceAgent`, `ContractAgent`, `WatchAgent`)
sont tous livrés. `DraftingAgent`, `StrategyAgent` et
`CollaborationAgent` restent, eux, hors de ce roadmap de 41 sprints
(voir la note de révision après le Sprint 29 dans
docs/09-roadmap-30-sprints.md).
