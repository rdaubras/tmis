# Rapport d'audit — Sprint 29 (Intégration agents métier + Agent Analyse)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« Phase 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), ce qui
existe déjà pour chacun des fichiers désignés par le prompt, confirme
qu'aucun n'a changé de forme depuis son sprint d'origine, et documente
deux écarts de contexte trouvés en cours d'audit (aucun bloquant).

## Fichiers désignés par le prompt : forme confirmée, aucun écart

| Fichier | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `tmis.agents.analysis_agent.AnalysisAgent` | Placeholder Sprint 1 : `result={"entities": [], "inconsistencies": []}`, confiance `LOW`, un avertissement fixe | Confirmé — remplacé par ce sprint |
| `tmis.agents.orchestrator.Orchestrator` | Graphe LangGraph `analysis -> verifier -> END`, constructeur acceptant déjà `analysis_agent`/`verifier_agent` optionnels | Confirmé inchangé dans sa mécanique ; docstring étendu (voir rapport d'architecture) |
| `tmis.agents.contracts` | Ré-export de `AgentInput`/`AgentOutput`/`AgentPort`/`ConfidenceLevel` depuis `tmis.ai.schemas.agent` | Confirmé, aucune modification |
| `tmis.ai.schemas.agent.AgentInput/AgentOutput/AgentPort` | `AgentInput(task_id, case_id, context)`, `AgentOutput(result, citations, confidence, warnings)`, `AgentPort` = `Protocol` avec `name` + `async def run(agent_input) -> AgentOutput` | Confirmé exact — **zéro changement de signature apporté** |
| `tmis.ai.kernel.kernel.TMISKernel.complete()` | `complete(prompt, *, provider=None, use_cache=True) -> ModelResponse`, seul point d'appel à un `ProviderRegistry`, cache + évaluation intégrés | Confirmé — c'est l'unique point d'appel utilisé par `AnalysisAgent` |
| `tmis.document_intelligence.storage.ports.DocumentStorePort` | `save`/`get`/`list_ids`, `Protocol` | Confirmé exact |
| `tmis.case_intelligence.cases.ports.CaseStorePort` | `get`/`save`/`get_or_create`/`list_ids`, `Protocol` | Confirmé exact |
| `tmis.ai_team.coordinator.*` / `tmis.ai_team.planner.*` | `CoordinatorEngine`/`Planner` : décomposition de missions multi-agents, file de travail, délégation — **le Coordinateur ne lance jamais d'analyse lui-même** (`_build_synthesis` ne fait que concaténer) | Confirmé inchangé ; voir « écart de contexte » ci-dessous sur son usage réel dans ce sprint |
| `tmis.platform_sdk.agent_sdk.base.BaseAgentPlugin` | `ABC` avec `run(context: PluginContext, agent_input: AgentInput) -> AgentOutput`, adaptateur `invoke()` vers le contrat `PluginPort` uniforme | Confirmé exact ; voir « écart de contexte » ci-dessous sur son non-usage dans ce sprint |
| `tmis.ai_fabric.fabric.AIIntelligenceFabric` | Façade composant `router`/`planner`/`critic`/`comparison`/`consensus`/`fusion` ; `route(request) -> RoutingDecision` | Confirmé exact |
| `tmis.ai_governance.overview.AIGovernancePlatform` | Façade composant 7 moteurs de gouvernance déjà persistés, dont `explainability: ExplainabilityEngine` | Confirmé exact |
| `tmis.strategic_intelligence.overview.StrategicIntelligencePlatform` | Façade composant `hypothesis_lab`/`action_planner`/`review`/`learning` | Confirmé exact ; non utilisé par `AnalysisAgent` (voir plus bas) |
| `tmis.workflow_automation.event_bus.WorkflowEventBus` | Bus pub/sub in-memory pour événements de workflow | Confirmé exact ; non utilisé par `AnalysisAgent` (voir plus bas) |
| `tmis.integration_hub.connector_framework.*` | `ConnectorPort` (auth/read/write, CRUD complet contre un système externe) | Confirmé exact ; non utilisé par `AnalysisAgent` (voir plus bas) |

Aucun de ces fichiers n'avait une forme différente de celle attendue —
aucun arbitrage utilisateur n'a donc été nécessaire avant de commencer.

## `tmis.domain.case_analysis` : mort, confirmé par recherche directe

Le module ne contient qu'un docstring de contexte borné (« Implementation
scheduled in a future sprint »), aucun code. Une recherche de
`from tmis.domain.case_analysis` / `import tmis.domain.case_analysis` sur
tout le dépôt (`src/` et `tests/`) ne retourne **aucun résultat** : ce
module n'est importé nulle part, y compris par ce sprint. Conformément à
la consigne du prompt, il n'a reçu aucun code et n'a pas été supprimé —
cette décision (le supprimer ou le laisser en l'état) reste hors du
périmètre de ce sprint et est signalée ici pour arbitrage ultérieur de
l'utilisateur.

## Écarts de contexte identifiés (aucun bloquant)

### 1. `platform_sdk.agent_sdk.BaseAgentPlugin` n'est pas « déjà le patron utilisé par un agent existant »

Le prompt conditionne l'usage de `platform_sdk.agent_sdk` à la
confirmation, en Phase 0, que c'est déjà le patron d'un agent existant.
Une recherche de `BaseAgentPlugin` dans tout `src/` montre qu'il n'est
sous-classé que par deux plugins de **démonstration** du Marketplace
(`platform_sdk.examples.agent_fiscal.AgentFiscalPlugin`,
`agent_droit_social.AgentDroitSocialPlugin`, tous deux Sprint 13) —
jamais par un agent de `tmis.agents` ni par un agent `tmis.ai_team`
(qui implémentent respectivement `AgentPort` directement et
`TeamAgentPort` via `tmis.ai_team.agents.kernel_adapter.
KernelAgentAdapter`). La méthode abstraite de `BaseAgentPlugin` a la
signature `run(context: PluginContext, agent_input: AgentInput) ->
AgentOutput` — incompatible avec `AgentPort.run(agent_input) ->
AgentOutput` que `Orchestrator._build_graph` invoque directement
(`await self._analysis_agent.run(state["agent_input"])`). L'utiliser
pour `AnalysisAgent` aurait donc exigé de changer soit la signature
appelée par l'`Orchestrator`, soit celle de `BaseAgentPlugin` — les deux
exclues par la contrainte « zéro changement de signature » de ce sprint.

**Décision** : `AnalysisAgent` reste un `AgentPort` nu, enregistré
directement (constructeur de l'`Orchestrator`), sans passer par
`platform_sdk.agent_sdk`. Voir docs/157-architecture-agent-analyse.md,
section dédiée.

### 2. Trois des sept plateformes listées ne s'appliquent pas à ce que `AnalysisAgent` fait réellement

Le prompt liste 7 plateformes disponibles « pour tout choix de modèle »,
« toute exigence d'explicabilité », « toute proposition de stratégie »,
« toute automatisation déclenchée », « tout échange avec un système
externe » — une disponibilité conditionnelle, pas une obligation
d'intégration systématique. `AnalysisAgent` lit des données déjà
persistées (`DocumentStorePort`/`CaseStorePort`) et produit un résultat
d'extraction ; il ne propose aucune stratégie, ne déclenche aucune
automatisation, et n'échange avec aucun système externe. En conséquence :

- `strategic_intelligence.overview.StrategicIntelligencePlatform` n'est
  pas câblé : aucune proposition de stratégie à produire.
- `workflow_automation.event_bus.WorkflowEventBus` n'est pas câblé :
  `AnalysisAgent` est plutôt le type d'action que Sprint 17 décrit comme
  *déclenchée par* un workflow (« import de document → analyse
  automatique »), pas un déclencheur d'automatisation lui-même.
- `integration_hub.connector_framework.ConnectorPort` n'est pas câblé :
  aucun système externe consulté — `DocumentStorePort`/`CaseStorePort`
  sont des ports internes (Sprint 26), pas des connecteurs LIH.

`tmis.ai_fabric.fabric.AIIntelligenceFabric` et `tmis.ai_governance.
overview.AIGovernancePlatform` sont, eux, réellement câblés — voir
docs/157-architecture-agent-analyse.md.

`tmis.ai_team.coordinator`/`.planner` ne sont pas non plus invoqués par
`AnalysisAgent` lui-même : ce sont les briques d'orchestration de
missions multi-agents (Sprint 11, `CoordinatorEngine.run_mission`), un
mécanisme distinct de l'`Orchestrator` LangGraph (Sprint 1) que ce sprint
étend. Les deux coexistent par conception dans le dépôt depuis le
Sprint 11 (confirmé par lecture : `CoordinatorEngine` accepte des
`TeamAgentPort` génériques dans un `dict`, sans référence à
`tmis.agents.Orchestrator`) — construire une seconde orchestration ici
aurait été la duplication que le prompt demande justement d'éviter, pas
son absence.

## Correction des références de sprint obsolètes (docstrings uniquement, comportement inchangé)

Les 9 agents placeholders autres que `AnalysisAgent` référençaient
chacun un numéro de sprint issu d'une révision antérieure de la roadmap
(avant les insertions des Sprints 6/7/8/10/11/... qui ont décalé toute la
numérotation). Recherche par `grep` : aucun ne référençait littéralement
« Sprint 11 » (seul `analysis_agent.py` le faisait, remplacé par ce
sprint) — chacun avait son propre numéro obsolète, corrigé vers la table
à jour (docs/09-roadmap-30-sprints.md) :

| Agent | Ancien numéro (docstring) | Numéro à jour |
|---|---|---|
| `SynthesisAgent` | Sprint 12 | Sprint 30 |
| `VerifierAgent` | Sprint 13 | Sprint 31 |
| `ResearchAgent` | Sprint 15 | Sprint 33 |
| `JurisprudenceAgent` | Sprint 16 | Sprint 34 |
| `ContractAgent` | Sprint 17 | Sprint 35 |
| `WatchAgent` | Sprint 21 | Sprint 36 |
| `DraftingAgent` | Sprint 18 | Hors roadmap actuelle (moteur déjà livré Sprint 7 ; aucun sprint Phase 3 ne cible un agent de rédaction) |
| `StrategyAgent` | Sprint 19 | Hors roadmap actuelle (absorbé par le Sprint 6, `tmis.legal_reasoning`) |
| `CollaborationAgent` | Sprint 20 | Hors roadmap actuelle (absorbé par le Sprint 8, `tmis.collaboration`) |

Seul le texte des docstrings (et le message de la `NotImplementedError`
correspondante) a changé — aucun de ces 9 agents n'a reçu de code
d'implémentation. Le prompt de ce sprint n'énumère explicitement que
« stratégie/collaboration hors roadmap actuelle » ; l'audit montre que
`DraftingAgent` est dans la même situation (aucun sprint Phase 3 actuel
ne le cible) — signalé ici en toute transparence plutôt que silencieusement
aligné sur une supposition non vérifiée.

## Test existant nécessairement mis à jour (pas laissé « inchangé »)

`tests/unit/test_orchestrator.py::test_orchestrator_runs_analysis_then_verifier`
asserte `any("placeholder" in warning for warning in output.warnings)` —
un texte qui n'a de sens que pour l'ancien placeholder. Le remplacer par
une extraction réelle rend cette assertion littéralement fausse quel que
soit le comportement (il n'y a plus de "placeholder"). L'intention du
test — vérifier que le câblage `analysis -> verifier` fonctionne toujours
de bout en bout — est préservée : le test appelle toujours
`Orchestrator()` sans injection, avec un `AgentInput` sans `document_id`
dans `context`, ce qui produit désormais une confiance `LOW` avec un
avertissement explicite sur l'absence de référence de document plutôt que
le texte "placeholder". Seule cette assertion de contenu a changé ; la
structure du test (mêmes objets construits, même appel, même assertion de
confiance `LOW`) reste identique.

## Conclusion

Aucun écart de forme trouvé sur les 12 fichiers désignés par le prompt —
tous ont exactement la forme attendue. Deux points de contexte identifiés
et documentés sans bloquer : `platform_sdk.agent_sdk.BaseAgentPlugin`
n'est pas le patron d'un agent existant comparable (signature
incompatible avec `AgentPort`), et 3 des 7 plateformes listées ne
s'appliquent pas fonctionnellement à ce que `AnalysisAgent` fait
réellement. `tmis.domain.case_analysis` est confirmé mort (aucun
importeur dans tout le dépôt) et signalé pour arbitrage plutôt que
modifié sans autorisation.
