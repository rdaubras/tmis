# Rapport d'architecture — Sprint 29 (Intégration agents métier + Agent Analyse)

## Résumé

Le Sprint 29 est un sprint de câblage, comme annoncé par la roadmap : il
relie **un seul agent réel**, `AnalysisAgent`, aux plateformes déjà
livrées par les sprints précédents (`TMISKernel`, Sprint 2 ;
`DocumentStorePort`/`CaseStorePort`, Sprint 26 ; `AIIntelligenceFabric`,
Sprint 14 ; `AIGovernancePlatform`, Sprint 15) — aucune de ces plateformes
n'a changé de signature. La Phase 0 de re-audit
(docs/reports/sprint-29-rapport-audit.md) a confirmé que les 12 fichiers
désignés par le prompt avaient exactement la forme attendue, avec deux
points de contexte documentés (aucun bloquant) : `platform_sdk.agent_sdk`
n'est pas le patron d'un agent comparable existant, et 3 des 7 plateformes
listées ne s'appliquent pas fonctionnellement à ce que `AnalysisAgent`
fait réellement.

Périmètre livré : `agents/analysis_agent.py` (réécrit intégralement),
`agents/orchestrator.py` (docstring étendu, mécanique inchangée), 9
docstrings d'agents placeholders corrigées (référence de sprint obsolète
uniquement), 9 tests unitaires + 1 test d'intégration bout-en-bout, 1
assertion de test existant mise à jour (voir le rapport d'audit).

## Décisions structurantes

### Un seul agent réel, pas neuf — le périmètre strict du prompt est respecté à la lettre

`SynthesisAgent`, `VerifierAgent`, `ResearchAgent`, `JurisprudenceAgent`,
`DraftingAgent`, `ContractAgent`, `StrategyAgent`, `WatchAgent`,
`CollaborationAgent` restent exactement les placeholders Sprint 1
(`raise NotImplementedError`, aucune ligne de logique). Seules leurs
docstrings ont été corrigées pour référencer le bon numéro de sprint (ou
« hors roadmap actuelle » — voir le rapport d'audit) ; aucun de ces 9
fichiers n'a reçu de code d'implémentation. C'est la même discipline déjà
appliquée aux Sprints 22 et 25 : ne jamais absorber par anticipation le
travail d'un sprint dédié sans une note de révision explicite qui le
documente.

### L'extraction réutilise le Document Intelligence Engine et le Case Intelligence Engine — elle ne les reconstruit jamais

`AnalysisAgent` ne réimplémente ni un extracteur d'entités ni un
détecteur d'incohérences. Il lit :

- `DocumentRecord.entities` (`ExtractedEntity`, Sprint 3) — regroupées par
  `EntityType` en catégories métier (personnes, sociétés, dates,
  montants, juridictions, contrats/références) ;
- `CaseProfile.timeline`/`.timeline_inconsistencies` (Sprint 4) si un
  `case_id` est fourni — la chronologie retombe sur
  `DocumentRecord.timeline_events` sinon, puisqu'il n'y a alors pas de
  dossier consolidé à consulter.

Le seul traitement réellement nouveau est le regroupement/formatage pour
le contrat `AgentOutput` et la synthèse narrative générative — jamais une
seconde extraction d'entités ou une seconde détection d'incohérences.

### `TMISKernel.complete()` reste l'unique point d'appel générique à un modèle

`AnalysisAgent._generate_narrative` appelle `self._kernel.complete(prompt,
provider=provider_name)` — même méthode que le nœud de démonstration
`ai.langgraph.nodes.make_analysis_node` (Sprint 2), même traitement du
texte retourné (stocké tel quel dans `result`, pas de parsing JSON strict
imposé au modèle). Les fournisseurs actuels (`OpenAIProvider`,
`AnthropicProvider`, `MistralProvider`, `LocalProvider`) restent des
échos déterministes Sprint 2 (« no real inference call ») — confirmé par
lecture avant d'écrire le prompt, pour ne pas concevoir un parseur JSON
strict qu'aucun fournisseur actuel ne peut satisfaire. Le prompt envoyé
au modèle synthétise les entités déjà regroupées, les incohérences déjà
détectées, et un extrait du texte du document — la valeur ajoutée
générative porte sur la synthèse narrative, pas sur la ré-extraction de
ce que le DIE/CIE fournissent déjà de façon fiable.

### Le choix du modèle passe par `AIIntelligenceFabric.route()`, jamais par un fournisseur fixe

`_route_model()` construit un `RoutingRequest(firm_id, task_type=
"document_analysis", prompt)` et appelle `self._fabric.route(request)`.
`RoutingDecision.model` (un `ModelDescriptor`) porte à la fois `.name` et
`.provider` — un seul appel à `route()` suffit pour obtenir le nom du
modèle choisi *et* le nom du fournisseur à passer à `TMISKernel.
complete(provider=...)`, sans second aller-retour dans le registre de
modèles. `self._fabric` reste optionnel (`AIIntelligenceFabric | None`) :
sans Fabric injecté, `_route_model` retombe sur `("default", None)` —
`TMISKernel.complete(prompt, provider=None)` utilise alors
`self.config.default_provider`, le comportement Sprint 2 préexistant,
jamais un fournisseur codé en dur par cet agent.

### L'explicabilité passe par `AIGovernancePlatform.explainability`, jamais par une gouvernance parallèle

`_record_explainability()` appelle `self._governance.explainability.
generate(firm_id, str(task_id), summary=..., steps_followed=(...),
agents_involved=("analysis",), models_used=(model_name,),
documents_consulted=(document_id,))` — la même `ExplainabilityEngine`
(Sprint 15) que consulte `AIGovernancePlatform.overview()`. `self.
_governance` reste optionnel : sans plateforme injectée, aucun rapport
n'est généré (l'agent reste utilisable en isolation, ex. dans les tests
unitaires qui n'exercent pas cette facette). Le rapport reste consultable
ensuite via `governance.explainability.latest(firm_id, str(task_id))` —
vérifié par le test d'intégration.

### Pourquoi pas `platform_sdk.agent_sdk.BaseAgentPlugin`

Voir la section dédiée du rapport d'audit et docs/157, section « Pourquoi
pas `BaseAgentPlugin` » — sa signature `run(context, agent_input)` est
incompatible avec `AgentPort.run(agent_input)` qu'`Orchestrator` invoque
directement ; l'utiliser aurait changé un contrat que ce sprint doit
laisser intact.

### `Orchestrator` : la mécanique ne change pas, le docstring documente le patron

`Orchestrator._build_graph` ne change pas : le nœud `"analysis"` appelait
déjà `self._analysis_agent.run(state["agent_input"])`, ce qui est
maintenant réellement `AnalysisAgent.run()` plutôt que le placeholder —
zéro ligne de `_build_graph` modifiée. Seul le docstring de la classe est
étendu avec la procédure en 4 étapes pour ajouter un futur agent au même
graphe (Sprint 30 et suivants) sans changer `OrchestratorState` ni la
signature publique `run()` — le livrable "patron" demandé par ce sprint,
sans construire de mécanisme d'extension supplémentaire (le constructeur
acceptait déjà des agents injectables depuis le Sprint 1).

## Test existant modifié (documenté, pas laissé silencieusement inchangé)

`test_orchestrator_runs_analysis_then_verifier` asserte désormais un
avertissement contenant `"document_id"` plutôt que `"placeholder"` — le
texte de l'ancien placeholder n'a plus de sens une fois l'extraction
réelle en place. La structure et l'intention du test (vérifier que le
graphe `analysis -> verifier` fonctionne bout en bout, confiance `LOW`
quand aucun document n'est fourni) sont inchangées ; seule l'assertion de
contenu textuel a été mise à jour. Voir le rapport d'audit pour le
raisonnement complet.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `tmis.agents.analysis_agent.AnalysisAgent` (réécrit) | `TMISKernel.complete()` (Sprint 2), `DocumentStorePort`/`CaseStorePort` (Sprint 26), `DocumentRecord.entities`/`.timeline_events` (Sprint 3), `CaseProfile.timeline`/`.timeline_inconsistencies` (Sprint 4), `AIIntelligenceFabric.route()` (Sprint 14), `AIGovernancePlatform.explainability` (Sprint 15) | Un second extracteur d'entités, un second détecteur d'incohérences, un second client LLM, un second routeur de modèle, une gouvernance de production parallèle |
| `tmis.agents.orchestrator.Orchestrator` (docstring uniquement) | Le patron déjà existant (constructeur avec agents injectables, graphe LangGraph) | Un second mécanisme d'extension du graphe |

## Vérification finale

- `ruff check src tests` → All checks passed
- `mypy src` (strict, 1890 fichiers) → Success, aucune erreur
- `pytest` → 2084 tests passants, 7 skipped (préexistants, gatés par
  `TMIS_REDIS_URL`/`TMIS_RUN_MODEL_DOWNLOAD_TESTS`, même patron que les
  Sprints 26-28), aucune régression
- Couverture globale : 96 % (seuil CI 90 %) ; `agents/analysis_agent.py` :
  100 % (100 énoncés, 0 manqués) ; `agents/orchestrator.py` : 100 %
- Vérification manuelle bout en bout : un `DocumentRecord` sauvegardé via
  `InMemoryDocumentStore.save()` (implémentation par défaut de
  `DocumentStorePort`), analysé via `Orchestrator(analysis_agent=
  AnalysisAgent(kernel=TMISKernel(), document_store=..., governance=
  get_ai_governance_platform())).run(agent_input)`, produit un
  `AgentOutput` avec entités groupées par type, une citation traçable
  vers le document source, une synthèse narrative non vide, et un
  rapport d'explicabilité consultable via `governance.explainability.
  latest(firm_id, str(task_id))` — voir
  `tests/integration/agents/test_analysis_agent_integration.py`.

## Confirmation explicite de périmètre

- Seul `AnalysisAgent` a été implémenté. `SynthesisAgent`,
  `VerifierAgent`, `ResearchAgent`, `JurisprudenceAgent`,
  `DraftingAgent`, `ContractAgent`, `StrategyAgent`, `WatchAgent`,
  `CollaborationAgent` restent des placeholders Sprint 1 inchangés dans
  leur comportement (`raise NotImplementedError`) — seules leurs
  docstrings ont été corrigées (référence de sprint).
- Aucune signature de `AgentInput`, `AgentOutput`, ou `AgentPort`
  (`tmis.ai.schemas.agent`) n'a changé.
- Aucun second client LLM, aucun second routeur de modèle, aucune
  seconde façon de déclencher une automatisation ou de valider une
  réponse IA n'a été introduit — tout passe par les plateformes déjà
  listées en Phase 0.
