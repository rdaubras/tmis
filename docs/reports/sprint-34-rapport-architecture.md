# Rapport d'architecture — Sprint 34 (Agent Jurisprudence, réel)

## Résumé

Le Sprint 34 relie `JurisprudenceAgent` (placeholder depuis le Sprint 1)
aux plateformes déjà livrées, en combinant les deux patrons de câblage
déjà établis : celui de `ResearchAgent` (Sprint 33) pour la recherche de
décisions, filtrée sur le connecteur `"jurisprudence"` déjà partagé par le
Kernel, et celui de `AnalysisAgent` (Sprint 29) pour la comparaison
générative de ces décisions — le seul travail réellement nouveau de ce
sprint. La Phase 0 de re-audit
(`docs/reports/sprint-34-rapport-audit.md`) a confirmé que les fichiers
désignés avaient le contenu attendu, y compris la « découverte clé »
annoncée par le prompt (le connecteur `"jurisprudence"` est déjà
enregistré sur le `ConnectorManager` du Kernel et donc déjà cherchable via
`ResearchOrchestrator.search()`), et a identifié un écart structurel —
hérité à l'identique du Sprint 33 — tranché avant tout code.

Périmètre livré : `tmis/agents/jurisprudence_agent.py` (réécrit,
placeholder -> implémentation réelle), `tmis/agents/citations.py`
(nouveau, adaptateur `research_citation_to_citation` extrait de
`ResearchAgent`), `tmis/agents/research_agent.py` (modifié pour appeler
l'adaptateur partagé au lieu de sa propre méthode statique),
`tmis/agents/bootstrap.py` (ajout de `get_jurisprudence_agent()`), 20
tests unitaires + 3 tests d'intégration nouveaux, 0 test existant
modifié dans son intention (seul un test d'intégration a dû changer de
requête, voir « Ajustement de test » ci-dessous),
docs/162-architecture-agent-jurisprudence.md, note de révision dans
docs/09-roadmap-30-sprints.md.

**Aucun autre agent de `tmis.agents` touché. `ResearchOrchestrator` et son
pipeline interne non modifiés. `Orchestrator` (LangGraph) non modifié.
Zéro changement de signature sur `AgentInput`/`AgentOutput`/`AgentPort`/
`ResearchOrchestrator.search()`/`Citation`/`ResearchCitation`/
`ChatMessageRequest`.**

## Décisions structurantes

### La recherche n'est qu'un filtre de connecteur — aucune nouvelle logique de recherche

La Phase 0 a tracé la chaîne complète confirmant la découverte clé du
prompt : `get_kernel()` construit `ConnectorManager(codes=...,
jurisprudence=build_jurisprudence_connector(), doctrine=...)` — la clé
`"jurisprudence"` existe dès la construction du Kernel — et
`get_research_orchestrator()` réutilise ce même `kernel.connector_manager`
pour son `HybridResearchSearch`. `ResearchOrchestrator.search()` acceptait
déjà `connector_names: list[str] | None` avant ce sprint, relayé sans
transformation jusqu'à `ConnectorManager.search(connector_names=...)`, qui
restreint alors la recherche à cette seule entrée.

**Décision** : `JurisprudenceAgent.run()` appelle
`self._orchestrator.search(query, connector_names=["jurisprudence"],
case_id=case_id)` — une seule différence avec `ResearchAgent.run()` :
`connector_names`. Aucune nouvelle classe, aucun nouveau port, aucun
paramètre ajouté à une signature existante. Vérifié par test
(`test_jurisprudence_agent_filters_search_on_the_jurisprudence_connector`,
qui espionne `connector_names` reçu par un `ResearchSearchPort` de test).

### L'adaptateur de citations extrait en fonction partagée — pas une copie, une réutilisation littérale

Le prompt interdit explicitement un second chemin de conversion de
citations, tout en autorisant l'extraction en fonction partagée « si la
duplication devient nécessaire — décision à documenter, pas à
improviser ». Recopier `ResearchAgent._to_citation` telle quelle dans
`JurisprudenceAgent` aurait été exactement la duplication interdite (même
logique, même docstring, deux définitions divergentes possibles à la
prochaine modification).

**Décision** : extraction de la méthode statique privée
`ResearchAgent._to_citation` vers `tmis.agents.citations.
research_citation_to_citation(result, citation)`, une fonction de module
sans état. `ResearchAgent` est modifié pour l'appeler au lieu de sa propre
méthode (comportement identique, un seul chemin de conversion),
`JurisprudenceAgent` l'appelle de la même façon. Alternative rejetée :
laisser l'adaptateur dans `research_agent.py` et l'importer directement
depuis `jurisprudence_agent.py` (`from tmis.agents.research_agent import
ResearchAgent` puis `ResearchAgent._to_citation`) — rejetée parce
qu'accéder à une méthode privée (`_`-préfixée) d'une autre classe à
travers un import direct est un couplage fragile que Python ne protège
pas, alors qu'une fonction de module explicitement publique documente
l'intention de partage. Vérifié par test
(`test_jurisprudence_agent_runs_a_real_search_and_converts_citations`,
identique dans sa forme au test équivalent de `ResearchAgent`) et par
`grep -rn "research_citation_to_citation" src/tmis/agents/` qui ne montre
qu'une définition et deux appels.

### La comparaison générative suit le patron `AnalysisAgent` — un seul appel `TMISKernel.complete()`, jamais deux

Le prompt exige « un seul point d'appel génératif (`TMISKernel.
complete()` via `AIIntelligenceFabric.route()`) pour la comparaison —
jamais deux ». `JurisprudenceAgent._generate_comparison()` reproduit
exactement `AnalysisAgent._generate_narrative()`/`_route_model()` :
`RoutingRequest(firm_id, "jurisprudence_comparison", prompt)` (un
`task_type` propre à ce sprint, `RoutingRequest.task_type` étant une
chaîne libre non contrainte par une énumération — confirmé par lecture de
`tmis.ai_fabric.router.schemas`/`engine`) puis `self._kernel.
complete(prompt, provider=decision.model.provider)`. Sans `fabric`
injecté (paramètre optionnel, comme `AnalysisAgent`), le routage retombe
sur `"default", None` — `TMISKernel.complete()` utilise alors son
provider par défaut plutôt que d'échouer. Vérifié par test
(`test_jurisprudence_agent_generates_a_comparison_without_a_fabric` et
`test_jurisprudence_agent_routes_comparison_through_the_fabric`).

### Aucune comparaison générée quand il n'y a rien à comparer

Contrairement à `AnalysisAgent` (qui génère toujours une narrative dès
qu'un document existe, même sans entité), une comparaison sur zéro
décision de jurisprudence n'a pas de sens et gaspillerait un appel
`TMISKernel.complete()`.

**Décision** : `_generate_comparison()` n'est appelé que si
`response.results` est non vide ; sinon `AgentOutput.result["comparison"]`
et `result["model"]` valent `None`, et un avertissement explicite est
ajouté (`"No jurisprudence result found for query {query!r}: nothing to
compare."`) — même principe de dégradation gracieuse que `ResearchAgent`
sur une recherche sans résultat. Vérifié par test
(`test_jurisprudence_agent_reports_low_confidence_when_the_lre_finds_
nothing`, qui vérifie aussi que `report.steps_followed` ne mentionne
jamais de comparaison générée dans ce cas —
`test_jurisprudence_agent_records_explainability_without_generation_
when_empty`).

### `CaseStorePort` injecté pour la pertinence par rapport au dossier — optionnel, comme pour `AnalysisAgent`

La mission demande explicitement que la comparaison évalue « la
pertinence par rapport au dossier ». `JurisprudenceAgent` lit donc
`CaseStorePort.get(case_id)` (même port que `AnalysisAgent`, défaut
`InMemoryCaseStore()`) si `agent_input.case_id` est fourni, et injecte le
titre du dossier plus un résumé chiffré (nombre d'acteurs, de faits) dans
le prompt de comparaison. Un `case_id` fourni mais introuvable ne bloque
jamais la comparaison — elle s'exécute quand même, sans le contexte du
dossier, avec un avertissement explicite (`"Case {case_id} was not found
in the case store."`), même patron que `AnalysisAgent` sur un `case_id`
introuvable. Vérifié par test
(`test_jurisprudence_agent_uses_case_profile_when_case_id_is_known`,
`test_jurisprudence_agent_warns_when_case_id_not_found`).

### `JurisprudenceAgent` n'est câblé ni dans l'`Orchestrator` ni dans le mode `"research"` du chat

Deux extensions que la mission autorisait de façon conditionnelle
(« sauf si la Phase 0 démontre que c'est trivial et strictement
additif »), toutes deux tranchées en faveur du statu quo :

- **`Orchestrator` (graphe LangGraph)** : la Phase 0 a confirmé que
  `ResearchAgent` — le patron de référence explicite du prompt pour la
  partie recherche — n'a lui-même jamais été ajouté à ce graphe au Sprint
  33 : il reste exposé uniquement via `tmis.agents.bootstrap.
  get_research_agent()` et l'endpoint de chat. Ajouter `JurisprudenceAgent`
  au graphe aurait donc établi un précédent que le patron de référence
  lui-même ne suit pas, sans qu'aucune partie de la mission ne le demande
  explicitement.
- **Mode `"research"` du chat (Sprint 33)** : une extension triviale
  aurait consisté à ajouter un mode `"jurisprudence"` qui appelle
  `JurisprudenceAgent.run()` au lieu de `ResearchAgent.run()`. Mais la
  restitution attendue diffère structurellement : le mode `"research"`
  actuel (`ResearchResults`, frontend) affiche des résultats bruts, alors
  qu'une comparaison de jurisprudence a une forme différente (texte
  généré + résultats sourcés) qui mérite sa propre conception d'affichage
  plutôt qu'une réutilisation superficielle du composant existant. Ce
  n'est donc pas « strictement additif » au sens où la mission l'entend —
  documenté comme scope futur dans
  docs/162-architecture-agent-jurisprudence.md plutôt qu'improvisé.

### Confiance et explicabilité : mêmes formules que les sprints précédents

`_confidence_for()` est la cascade `LOW`/`MEDIUM`/`HIGH` exacte de
`ResearchAgent` (aucun résultat -> `LOW`, résultats frais -> `MEDIUM`,
`cache_hit=True` -> `HIGH`) : la confiance reflète la recherche, pas la
qualité de la comparaison générative — cohérent avec le fait qu'une
comparaison peut légitimement être `None` sans dégrader `confidence`
au-delà de ce que l'absence de résultats implique déjà.
`_record_explainability()` reprend le patron `AnalysisAgent`
(`steps_followed` détaillés, `models_used` conditionnel au modèle
effectivement appelé, `documents_consulted` sur les identifiants de
décisions) — optionnel comme pour les trois agents précédents.

## Ajustement de test : requête d'intégration alignée sur la fixture existante

Le premier jet du test d'intégration bout en bout utilisait la requête
« licenciement pour faute grave », choisie sans vérifier le contenu de la
fixture `JurisprudenceConnector` (Sprint 2) — `search_fixture()` fait une
recherche par sous-chaîne naïve sur `title`/`content`, et l'unique
document de la fixture (`"Décision de principe sur la responsabilité
contractuelle en cas d'inexécution."`) ne contient pas cette expression.
Corrigé en `"responsabilité contractuelle"`, qui matche le contenu réel
de la fixture — repéré immédiatement par l'échec du test en exécution
réelle (`assert output.result["results"]` -> `assert []`), pas une
supposition non vérifiée. Aucune ligne de production modifiée pour cet
ajustement, uniquement la requête du test.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `JurisprudenceAgent` (recherche) | `ResearchOrchestrator.search(connector_names=["jurisprudence"])`/`get_citations()` (Sprint 5, inchangés) | Un second moteur de recherche, un second connecteur jurisprudence, une seconde logique de classement/cache |
| `tmis.agents.citations.research_citation_to_citation` | Extrait de `ResearchAgent._to_citation` (Sprint 33) | Un second adaptateur `ResearchCitation -> Citation` |
| `JurisprudenceAgent` (comparaison) | `AIIntelligenceFabric.route()` (Sprint 14), `TMISKernel.complete()` (Sprint 2), `CaseStorePort` (Sprint 26) | Un second client LLM, un second routeur de modèle |
| `JurisprudenceAgent` (explicabilité) | `AIGovernancePlatform.explainability.generate()` (Sprint 15) | Une gouvernance de production parallèle |
| `tmis.agents.bootstrap.get_jurisprudence_agent` | `get_research_orchestrator()` (Sprint 5), `get_kernel()` (Sprint 2), `get_ai_intelligence_fabric()` (Sprint 14), `get_case_intelligence_workflow().case_store` (Sprint 4), `get_ai_governance_platform()` (Sprint 15) — même patron `@lru_cache` que `get_research_agent()` | Un second singleton d'orchestrateur, de Kernel, de Fabric ou de plateforme de gouvernance |

## Test existant modifié : un seul, dans sa donnée d'entrée uniquement

`tests/unit/agents/test_research_agent.py` et
`tests/integration/agents/test_research_agent_integration.py` restent
verts sans aucune modification (l'extraction de `_to_citation` en
fonction partagée est un renommage interne, le comportement observable de
`ResearchAgent` est strictement identique). Aucun autre test préexistant
n'a été touché.

23 tests nouveaux :

- `tests/unit/agents/test_jurisprudence_agent.py` (+15, nouveau
  fichier) : absence de `query` -> `LOW`, absence de résultat -> `LOW`
  sans génération, filtrage effectif sur `connector_names=
  ["jurisprudence"]`, recherche réelle avec conversion de citations
  vérifiée champ par champ, comparaison générée sans/avec `fabric`
  injecté, dossier connu/introuvable, transmission de `case_id` à
  l'historique de la LRE, explicabilité enregistrée avec et sans
  génération.
- `tests/integration/agents/test_jurisprudence_agent_integration.py`
  (+3, nouveau fichier) : bout en bout sur le vrai
  `get_research_orchestrator()` (mêmes connecteurs fixture que
  `test_research_agent_integration.py`), résultats et citations
  strictement filtrés sur `connector == "jurisprudence"`, comparaison
  générée via le vrai `TMISKernel.complete()`, `case_id` retrouvé dans
  l'historique réel, requête manquante -> résultat vide sans appeler la
  LRE.

## Vérification finale

- `pytest -q` (depuis `backend/`) → **2153 passed, 7 skipped** (2130
  tests préexistants + 23 nouveaux, 0 régression ; les 7 `skipped` sont
  préexistants, gatés par `TMIS_REDIS_URL`/
  `TMIS_RUN_MODEL_DOWNLOAD_TESTS`, non liés à ce sprint). Exécuté sur un
  environnement virtuel dédié reconstruit pour ce sprint (le système hôte
  porte un `PyJWT` installé par le gestionnaire de paquets système que
  `pip -e ".[dev]"` seul ne peut pas remplacer dans le même environnement).
- `ruff check src tests` (commande CI) → **All checks passed** (deux
  dépassements de longueur de ligne dans `jurisprudence_agent.py`,
  détectés et corrigés avant ce résultat final).
- `mypy src` (commande CI) → **Success: no issues found in 1896 source
  files** (première exécution sans cache sur l'ensemble du dépôt,
  plusieurs minutes du fait des dépendances lourdes telles que
  `torch`/`transformers`, mais concluante).
- Confirmation explicite de périmètre : `git diff --stat` sur
  `tmis/agents/` ne montre que `jurisprudence_agent.py` (réécrit),
  `citations.py` (nouveau), `research_agent.py` (modifié : extraction de
  l'adaptateur, aucun changement de comportement) et `bootstrap.py`
  (ajout de `get_jurisprudence_agent()`). `git diff --stat` sur
  `tmis/legal_research/`, `tmis/agents/orchestrator.py`,
  `tmis/ai_fabric/`, `tmis/ai/kernel/`, `tmis/ai_governance/`,
  `tmis/api/v1/chat/` est vide.
