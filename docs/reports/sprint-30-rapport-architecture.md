# Rapport d'architecture — Sprint 30 (Agent Synthèse narrative)

## Résumé

Le Sprint 30 est un sprint de câblage, comme annoncé par la roadmap : il
relie **un second agent réel**, `SynthesisAgent`, aux plateformes déjà
livrées par les sprints précédents (`TMISKernel`, Sprint 2 ;
`CaseStorePort`, Sprint 26 ; `CaseSummaryGenerator`, Sprint 4 ;
`WritingStyleEngine`, Sprint 12 ; `AIIntelligenceFabric`, Sprint 14 ;
`AIGovernancePlatform`, Sprint 15) — aucune de ces plateformes n'a changé
de signature. La Phase 0 de re-audit
(docs/reports/sprint-30-rapport-audit.md) a confirmé que les 11 fichiers
désignés par le prompt avaient exactement la forme attendue.

Périmètre livré : `agents/synthesis_agent.py` (réécrit intégralement),
`agents/orchestrator.py` (constructeur + `_build_graph` + docstring
étendus, nœud `"synthesis"` ajouté), 11 tests unitaires + 1 test
d'intégration bout-en-bout nouveaux, 0 test existant modifié.

## Décisions structurantes

### Un seul agent réel de plus, pas huit — le périmètre strict du prompt est respecté à la lettre

`VerifierAgent`, `ResearchAgent`, `JurisprudenceAgent`, `DraftingAgent`,
`ContractAgent`, `StrategyAgent`, `WatchAgent`, `CollaborationAgent`
restent exactement les placeholders (`raise NotImplementedError`, aucune
ligne de logique) — inchangés par ce sprint, y compris leurs docstrings
(déjà corrigées au Sprint 29). Seul `SynthesisAgent` a reçu une
implémentation réelle.

### La synthèse réutilise `CaseSummaryGenerator` — elle ne le reconstruit jamais

`SynthesisAgent` ne réimplémente ni un second générateur de résumé
exécutif ni une seconde agrégation chronologique/documentaire. Il appelle
`self._summary_generator.generate(case_profile)` (`SummaryGeneratorPort`,
injectable) et récupère `CaseSummary.executive_summary` /
`.chronological_summary` / `.documentary_summary` / `.case_status` /
`.open_points` tels quels — aucun second appel à `TMISKernel.complete()`
pour ce que `CaseSummaryGenerator` produit déjà (son unique appel de
modèle, pour le résumé exécutif, reste interne à
`CaseSummaryGenerator.generate()`).

Le seul traitement réellement nouveau est :

1. L'agrégation déterministe (aucun appel de modèle) des livrables que
   `CaseSummaryGenerator` ne produit pas : le tableau
   acteurs/faits/échéances (`result["table"]`, dont les « échéances »
   viennent de `CaseProfile.tasks` non terminées — un champ que
   `CaseSummaryGenerator` ne lit jamais, garantissant qu'il n'y a pas de
   double calcul), la fiche de synthèse (`result["fact_sheet"]`), et la
   checklist (`result["checklist"]`, fusion des `open_points` déjà
   calculés et des `CaseProfile.tasks`).
2. Une note de synthèse narrative (`result["synthesis_note"]`), seul
   second appel à `TMISKernel.complete()` du pipeline complet — justifié
   parce qu'il répond à un besoin que `CaseSummaryGenerator` ne couvre
   pas : la mise en forme selon le style rédactionnel du cabinet.

### Le style du cabinet est lu, jamais réécrit par `apply_style()`

`SynthesisAgent` appelle `self._writing_style_engine.get_or_create_profile
(firm_id, actor)` — une lecture idempotente qui ne requiert aucune
validation préalable (contrairement à `apply_style()`, qui lève
`WritingStyleNotValidatedError` sans profil validé). Le
`WritingStyleProfile` obtenu (`vocabulary`, `favorite_expressions`,
`structure_preferences`) est injecté comme instructions dans le prompt de
`_generate_synthesis_note` — jamais passé à `apply_style()`, dont le
docstring documente explicitement que cette méthode n'est *pas* une
réécriture générative (elle ajoute un bloc de signature déterministe,
« adapting an agent's drafting *voice* ... [is] kept out of scope »).
Respecter cette contrainte du prompt signifie concrètement : lire les
*données* du profil, jamais appeler cette méthode.

### `TMISKernel.complete()` reste l'unique point d'appel générique à un modèle

`SynthesisAgent._generate_synthesis_note` appelle `self._kernel.complete
(prompt, provider=provider_name)` — même méthode, même traitement du
texte retourné, que `AnalysisAgent` (Sprint 29) et
`CaseSummaryGenerator` (Sprint 4). Le prompt envoyé au modèle synthétise
le résumé exécutif déjà rédigé, les comptages du tableau, les points
ouverts, et les préférences de style du cabinet — jamais les données
brutes du dossier ré-analysées, pour ne pas dupliquer l'extraction déjà
faite par le Case Intelligence Engine.

### Le choix du modèle passe par `AIIntelligenceFabric.route()`, jamais par un fournisseur fixe

`_route_model()` reproduit exactement le patron `AnalysisAgent`
(`RoutingRequest(firm_id, task_type="case_synthesis", prompt)`,
`RoutingDecision.model.name`/`.provider` en un seul appel). `self._fabric`
reste optionnel ; sans Fabric injecté, retombe sur `("default", None)`.

### L'explicabilité passe par `AIGovernancePlatform.explainability`, jamais par une gouvernance parallèle

`_record_explainability()` appelle `self._governance.explainability.
generate(firm_id, str(task_id), summary=..., steps_followed=(...),
agents_involved=("synthesis",), models_used=(model_name,),
documents_consulted=tuple(case_profile.document_ids))`. Quand
`SynthesisAgent` et `AnalysisAgent` traitent la même tâche (même
`task_id`), les deux enregistrent un rapport sous le même `production_id`
— `ExplainabilityEngine.history()` conserve les deux, `latest()` ne
renvoie que le plus récent (celui de Synthèse, puisqu'elle s'exécute en
dernier dans le graphe) ; le test d'intégration vérifie `history()` pour
confirmer que les deux rapports coexistent, plutôt que de supposer que
`latest()` suffit.

### `Orchestrator` : nœud `"synthesis"` fusionné, pas remplacé — la seule déviation documentée du patron Sprint 29

Le docstring Sprint 29 documentait le patron générique : la closure
`run_<name>` appelle `.run(state["agent_input"])` et **remplace**
`state["output"]`. Appliqué littéralement à `"synthesis"` inséré entre
`"verifier"` et `END`, ce remplacement aurait cassé silencieusement deux
tests Sprint 29 existants (voir le rapport d'audit, section dédiée) :
`Orchestrator`'s output serait devenu celui de `SynthesisAgent` seul,
faisant disparaître les entités d'Analyse et faisant chuter la confiance
à `LOW` dès qu'aucun `case_id` n'est fourni — un cas parfaitement normal
pour une simple analyse de document sans dossier associé.

**Décision** : `run_synthesis` fusionne via `_fuse_with_synthesis(previous,
synthesis)` :
- `confidence` reste celle du Vérificateur (`previous.confidence`) —
  Synthèse répond à une question différente et son absence de matière (pas
  de `case_id`, dossier introuvable) n'est pas un signal de mauvaise
  qualité sur ce qu'Analyse a déjà établi ;
- `result` s'étend sous une clé `"synthesis"` dédiée
  (`{**previous.result, "synthesis": synthesis.result}`) — jamais
  d'écrasement des clés d'Analyse (`entities`, `narrative`, ...) ;
- `citations` et `warnings` sont concaténés (Analyse d'abord, puis
  Synthèse) — `output.citations[0]` reste donc la citation d'Analyse,
  préservant les assertions existantes qui l'indexent.

Cette fusion est la lecture correcte de « suivre exactement le patron » —
constructeur injectable (`synthesis_agent: SynthesisAgent | None = None`),
closure `run_synthesis`, arêtes (`"verifier" -> "synthesis" -> END`) —
sans reproduire aveuglément l'instantiation « remplacement » écrite pour
un agent générique hypothétique avant que les besoins réels de Synthèse
soient connus. `OrchestratorState` reste inchangé (toujours un seul
`AgentOutput | None`) ; le docstring de `Orchestrator` est mis à jour pour
documenter les deux variantes du patron (remplacement *ou* fusion) pour
les sprints suivants.

### Positionnement : après `"verifier"`, avant `END`

Choix explicitement suggéré par le docstring Sprint 29 lui-même
(« one that runs *after* Verifier ... is inserted between "verifier" and
END ») : `SynthesisAgent` consomme conceptuellement la sortie déjà
vérifiée du pipeline, et produit les livrables de synthèse comme dernière
étape d'un traitement de dossier — jamais avant que la fiabilité du
résultat primaire ait été évaluée.

## Test existant modifié : aucun

Contrairement au Sprint 29 (qui avait dû mettre à jour une assertion
`test_orchestrator_runs_analysis_then_verifier` sur un texte de placeholder
devenu obsolète), **aucun test existant n'a été modifié** par ce sprint.
La fusion (plutôt que le remplacement) documentée ci-dessus a été conçue
précisément pour préserver ce comportement — vérifié par exécution :
`test_orchestrator_runs_analysis_then_verifier` et
`test_persisted_document_flows_through_analysis_agent_and_verifier`
passent tels quels, avec le nœud `"synthesis"` désormais actif dans le
graphe qu'ils exercent.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `tmis.agents.synthesis_agent.SynthesisAgent` (réécrit) | `CaseStorePort` (Sprint 26), `CaseSummaryGenerator.generate()` (Sprint 4), `WritingStyleEngine.get_or_create_profile()` (Sprint 12), `TMISKernel.complete()` (Sprint 2), `AIIntelligenceFabric.route()` (Sprint 14), `AIGovernancePlatform.explainability` (Sprint 15) | Un second générateur de résumé exécutif, un second appel de modèle pour ce que `CaseSummaryGenerator` produit déjà, une réécriture générative via `apply_style()`, un second client LLM, un second routeur de modèle, une gouvernance de production parallèle |
| `tmis.agents.orchestrator.Orchestrator` (constructeur + `_build_graph` + docstring) | Le patron déjà existant (constructeur avec agents injectables, graphe LangGraph), étendu avec une variante « fusion » pour un nœud additif | Un second mécanisme d'extension du graphe, un second type d'état (`OrchestratorState` inchangé) |

## Vérification finale

- `ruff check src tests` → All checks passed
- `mypy src` (1890 fichiers) → Success, aucune erreur
- `pytest` → 2096 tests passants (2084 préexistants + 12 nouveaux : 11
  tests unitaires `SynthesisAgent` (`tests/unit/agents/
  test_synthesis_agent.py`) + 1 test d'intégration bout-en-bout
  (`tests/integration/agents/test_synthesis_agent_integration.py`)),
  7 skipped (préexistants, gatés par
  `TMIS_REDIS_URL`/`TMIS_RUN_MODEL_DOWNLOAD_TESTS`), aucune régression
- Couverture globale : 96 % (seuil CI 90 %) ; `agents/synthesis_agent.py` :
  100 % (103 énoncés, 0 manqués) ; `agents/orchestrator.py` : 100 %
- Vérification manuelle bout en bout : un `CaseProfile` sauvegardé via
  `InMemoryCaseStore.save()` (implémentation par défaut de
  `CaseStorePort`) et un `DocumentRecord` associé sauvegardé via
  `InMemoryDocumentStore.save()`, traités via
  `Orchestrator(analysis_agent=AnalysisAgent(kernel=TMISKernel(),
  document_store=..., governance=get_ai_governance_platform(),
  firm_id="firm-test"), synthesis_agent=SynthesisAgent(kernel=TMISKernel(),
  case_store=..., governance=get_ai_governance_platform(),
  firm_id="firm-test")).run(agent_input)`, produit un `AgentOutput` dont
  `result["entities"]` reste celui d'Analyse et `result["synthesis"]`
  porte le résumé exécutif réutilisé, le tableau acteurs/faits/échéances,
  la fiche de synthèse, la checklist, et la note de synthèse narrative —
  avec des rapports d'explicabilité consultables pour les deux agents via
  `governance.explainability.history(firm_id, str(task_id))` — voir
  `tests/integration/agents/test_synthesis_agent_integration.py`.

## Confirmation explicite de périmètre

- Seul `SynthesisAgent` a reçu une implémentation réelle ce sprint.
  `VerifierAgent`, `ResearchAgent`, `JurisprudenceAgent`, `DraftingAgent`,
  `ContractAgent`, `StrategyAgent`, `WatchAgent`, `CollaborationAgent`
  restent des placeholders inchangés (`raise NotImplementedError`) — pas
  une ligne de comportement modifiée, pas une docstring touchée (déjà à
  jour depuis le Sprint 29).
- Aucune signature de `AgentInput`, `AgentOutput`, `AgentPort`
  (`tmis.ai.schemas.agent`) ni de `SummaryGeneratorPort`/
  `SummaryKernelPort` (`tmis.case_intelligence.summaries.ports`) n'a
  changé.
- `WritingStyleEngine.apply_style()` n'a reçu aucune modification et n'a
  été appelé nulle part par ce sprint — seul `WritingStyleProfile` (les
  données) est lu, via `get_or_create_profile()`.
- Aucun second client LLM, aucun second routeur de modèle, aucun second
  générateur de résumé de dossier, aucune seconde façon de déclencher une
  automatisation ou de valider une réponse IA n'a été introduit — tout
  passe par les plateformes déjà listées en Phase 0.
