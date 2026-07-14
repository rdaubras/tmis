# Rapport d'audit — Sprint 30 (Agent Synthèse narrative)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« Phase 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), ce qui
existe déjà pour chacun des fichiers désignés par le prompt, et confirme
qu'aucun n'a changé de forme depuis son sprint d'origine.

## Fichiers désignés par le prompt : forme confirmée, aucun écart

| Fichier | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `tmis.agents.synthesis_agent.SynthesisAgent` | Placeholder Sprint 1 : `raise NotImplementedError("...Sprint 12...")`, aucune ligne de logique | Confirmé — remplacé par ce sprint ; le message d'erreur obsolète référençant « Sprint 12 » disparaît avec le fichier réécrit |
| `tmis.agents.orchestrator.Orchestrator` | Graphe LangGraph `analysis -> verifier -> END` (Sprint 29), constructeur acceptant `analysis_agent`/`verifier_agent` optionnels, docstring documentant explicitement le patron d'ajout d'un futur nœud (« Sprint 30 and later ») | Confirmé inchangé dans sa mécanique avant ce sprint ; docstring et `_build_graph` étendus par ce sprint (voir rapport d'architecture) |
| `tmis.agents.contracts` | Ré-export de `AgentInput`/`AgentOutput`/`AgentPort`/`ConfidenceLevel` depuis `tmis.ai.schemas.agent` | Confirmé, aucune modification |
| `tmis.agents.analysis_agent.AnalysisAgent` (patron de référence Sprint 29) | Câblage `TMISKernel`/`DocumentStorePort`/`CaseStorePort`/`AIIntelligenceFabric.route()`/`AIGovernancePlatform.explainability`, style de docstring, structure du `__init__` avec paramètres optionnels nommés (`kernel`, stores, `fabric`, `governance`, `firm_id`) | Confirmé exact — patron reproduit à l'identique pour `SynthesisAgent` (mêmes noms de paramètres, même ordre de construction, même structure de méthodes privées `_route_model`/`_confidence_for`/`_record_explainability`) |
| `tmis.case_intelligence.summaries.generator.CaseSummaryGenerator` | `generate(profile) -> CaseSummary` : résumé exécutif via `TMISKernel.complete()` (le seul des quatre champs qui appelle un modèle), les trois autres (chronologique, documentaire, statut, points ouverts) en agrégation déterministe pure | Confirmé exact — réutilisé tel quel par `SynthesisAgent`, aucun second appel de modèle pour ce chemin |
| `tmis.case_intelligence.summaries.ports.{SummaryKernelPort, SummaryGeneratorPort}` | `SummaryKernelPort.complete(prompt) -> ModelResponse` (sous-ensemble narrow de ce que `TMISKernel` expose) ; `SummaryGeneratorPort.generate(profile) -> CaseSummary` | Confirmé exact, aucune modification — `SynthesisAgent` accepte un `SummaryGeneratorPort` injectable, jamais un `CaseSummaryGenerator` concret en dur |
| `tmis.case_intelligence.summaries.schemas.CaseSummary` | `dataclass` frozen : `executive_summary`, `chronological_summary`, `documentary_summary`, `case_status`, `open_points` | Confirmé exact |
| `tmis.case_intelligence.cases.ports.CaseStorePort` | `get`/`save`/`get_or_create`/`list_ids`, `Protocol` | Confirmé exact, identique au Sprint 26 déjà utilisé par `AnalysisAgent` |
| `tmis.cabinet_knowledge.writing_style.engine.WritingStyleEngine` | `get_or_create_profile(firm_id, author) -> WritingStyleProfile` (lecture idempotente, ne requiert aucune validation), `update_profile(...)`, `apply_style(firm_id, draft_text) -> str` — **transformation déterministe** (ajout du bloc de signature validé), explicitement documentée comme n'étant *pas* une réécriture générative (« adapting an agent's drafting *voice* to the profile is a Legal Drafting Studio (Sprint 7) concern... kept out of scope here ») | Confirmé exact — `SynthesisAgent` utilise uniquement `get_or_create_profile()` (lecture de données) pour injecter `WritingStyleProfile.vocabulary`/`.favorite_expressions`/`.structure_preferences` dans le prompt ; `apply_style()` n'est ni appelé ni détourné |
| `tmis.cabinet_knowledge.writing_style.schemas.WritingStyleProfile` | `dataclass` frozen : `id`, `vocabulary`, `favorite_expressions`, `structure_preferences`, `signature_block` | Confirmé exact |
| `tmis.ai_fabric.fabric.AIIntelligenceFabric` | Façade composant `router`/`planner`/`critic`/`comparison`/`consensus`/`fusion` ; `route(request) -> RoutingDecision` | Confirmé exact, identique au Sprint 29 |
| `tmis.ai_governance.overview.AIGovernancePlatform` | Façade composant 7 moteurs de gouvernance déjà persistés, dont `explainability: ExplainabilityEngine` (`generate`/`history`/`latest`) | Confirmé exact, identique au Sprint 29 |

Aucun de ces fichiers n'avait une forme différente de celle attendue —
aucun arbitrage utilisateur n'a donc été nécessaire avant de commencer.

## Un point de vigilance identifié en cours d'implémentation (pas en Phase 0, mais avant tout commit)

Le prompt demande de suivre « exactement le patron documenté dans
`Orchestrator` au Sprint 29 » pour le nœud `"synthesis"`. Ce patron,
lu littéralement dans le docstring Sprint 29, dit : la closure
`run_<name>` appelle `self._<name>_agent.run(state["agent_input"])` et
retourne `{**state, "output": output}` — c'est-à-dire un **remplacement**
pur et simple de la sortie précédente.

Appliqué tel quel à `"synthesis"` inséré après `"verifier"`, ce
remplacement aurait cassé silencieusement deux tests Sprint 29 existants
que le prompt demande explicitement de garder passants :

- `test_orchestrator_runs_analysis_then_verifier` : le résultat final
  serait devenu celui de `SynthesisAgent` (appelé avec le même
  `AgentInput`, `case_id` aléatoire non résolu dans le store en mémoire
  par défaut), dont l'avertissement contient « Case ... was not found »
  au lieu de « document_id » — l'assertion `any("document_id" in
  warning ...)` aurait échoué.
- `test_persisted_document_flows_through_analysis_agent_and_verifier` :
  cet `AgentInput` a `case_id=None`, donc `SynthesisAgent` renvoie une
  confiance `LOW` par construction (« rien à synthétiser ») ; un
  remplacement pur aurait fait chuter la confiance finale de
  `MEDIUM`/`HIGH` à `LOW`, cassant l'assertion
  `output.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)`.

**Décision** : `run_synthesis` fusionne la sortie de `SynthesisAgent` dans
la sortie déjà vérifiée (`_fuse_with_synthesis`) plutôt que de la
remplacer — `previous.confidence` reste autoritaire, `result` est étendu
sous une clé `"synthesis"` dédiée, `citations`/`warnings` sont concaténés.
Les deux tests Sprint 29 ci-dessus passent alors **sans aucune
modification** (vérifié par exécution, voir rapport d'architecture). Ce
choix est documenté dans le docstring d'`Orchestrator` lui-même comme la
lecture correcte de « suivre exactement le patron » pour un agent qui
*ajoute* aux résultats précédents plutôt que d'en produire un remplaçant
— la même discipline de transparence que le rapport d'audit Sprint 29
appliquait déjà à `test_orchestrator_runs_analysis_then_verifier`
(assertion mise à jour, documentée, jamais laissée silencieusement
divergente).

## Conclusion

Aucun écart de forme trouvé sur les 11 fichiers désignés par le prompt —
tous ont exactement la forme attendue. Un point d'interprétation identifié
en cours d'implémentation (pas un écart de Phase 0) : le patron
« remplacement de sortie » documenté au Sprint 29 pour un nœud générique
devient une fusion pour `"synthesis"`, seule lecture compatible avec la
contrainte « les tests existants sur ... l'orchestrateur doivent continuer
à passer inchangés » — documenté ci-dessus et dans le rapport
d'architecture plutôt qu'appliqué silencieusement.
