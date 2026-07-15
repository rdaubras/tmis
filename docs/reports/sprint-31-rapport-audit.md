# Rapport d'audit — Sprint 31 (Agent Vérificateur enrichi)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« Phase 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), ce qui
existe déjà pour chacun des fichiers désignés par le prompt, et confirme
qu'aucun n'a changé de forme depuis son sprint d'origine.

## Fichiers désignés par le prompt : forme confirmée, aucun écart

| Fichier | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `tmis.agents.verifier_agent.VerifierAgent` | Placeholder Sprint 1 enrichi d'une seule vérification : `verify(output)` détecte les citations sans `excerpt`/`reference`, dégrade `HIGH -> MEDIUM` si `warnings` est non vide, `run()` lève `NotImplementedError` (non invoqué comme point d'entrée du graphe) | Confirmé — seule la vérification de citations existait ; enrichi par ce sprint |
| `tmis.agents.orchestrator.Orchestrator` | Graphe LangGraph `analysis -> verifier -> synthesis -> END` (Sprint 30), constructeur acceptant `analysis_agent`/`verifier_agent`/`synthesis_agent` optionnels, `run_verifier` câblé uniquement entre `"analysis"` et `"synthesis"` — **`verify()` n'est aujourd'hui jamais appelé sur la sortie de Synthesis** | Confirmé — c'est exactement le bug que ce sprint corrige (voir rapport d'architecture) |
| `tmis.agents.contracts` | Ré-export de `AgentInput`/`AgentOutput`/`AgentPort`/`ConfidenceLevel` depuis `tmis.ai.schemas.agent` | Confirmé, aucune modification |
| `tmis.agents.analysis_agent.AnalysisAgent` | `result` = `{"entities", "inconsistencies", "timeline", "narrative", "model"}` ; `narrative` est le seul champ texte réellement généré par `TMISKernel.complete()` (`_generate_narrative`) ; la citation attachée a `connector="document_store"`, `source_id=document.document_id` | Confirmé — `narrative` est bien la clé narrative d'Analyse ; aucune citation `case_store` n'y apparaît jamais, même quand `case_id` est fourni (l'agent ne cite jamais le dossier lui-même, seulement le document) |
| `tmis.agents.synthesis_agent.SynthesisAgent` | `result` = `{"executive_summary", "chronological_summary", "documentary_summary", "case_status", "open_points", "table", "fact_sheet", "checklist", "synthesis_note", "model"}` ; seuls `executive_summary` (via `CaseSummaryGenerator`, lui-même `TMISKernel.complete()`) et `synthesis_note` (`_generate_synthesis_note`, `TMISKernel.complete()`) sont du texte réellement généré par modèle — `chronological_summary`/`documentary_summary`/`case_status` sont des agrégations déterministes (`CaseSummaryGenerator._chronological_summary`/`._documentary_summary`/`._case_status`, aucun appel modèle) ; la citation finale a `connector="case_store"`, `source_id=case_profile.case_id` | Confirmé — deux clés narratives (`executive_summary`, `synthesis_note`), pas trois ; la citation `case_store` est la seule voie disponible pour retrouver un `case_id` depuis un `AgentOutput`, puisque `AgentOutput` lui-même n'a pas de champ `case_id` |
| `tmis.legal_reasoning.conflicts.engine.HeuristicConflictDetector` | Implémente `ConflictDetectorPort.detect(facts, timeline_inconsistencies) -> list[Conflict]` ; compose sur les données déjà consolidées par le Case Intelligence Engine (`Fact.contradicting_document_ids`, `TimelineInconsistency`), ne réextrait rien | Confirmé exact, `Protocol` inchangé |
| `tmis.legal_reasoning.conflicts.ports.ConflictDetectorPort` | `Protocol` à une méthode : `detect(facts, timeline_inconsistencies) -> list[Conflict]` | Confirmé exact, aucune modification |
| `tmis.legal_reasoning.conflicts.schemas.{Conflict, ConflictType}` | `Conflict` frozen : `id`, `type`, `description`, `explanation`, `involved_ids` ; `ConflictType` : `DOCUMENT_CONTRADICTION`, `TEMPORAL_CONTRADICTION`, `FACT_INCONSISTENCY`, `DUPLICATE` | Confirmé exact |
| `tmis.ai_governance.hallucination_detection.engine.HallucinationDetectionEngine` | `scan(text) -> list[HallucinationAlert]` : bâti sur `ResponseEvaluator` (Sprint 14), jamais un second compteur de citations — alerte si 0 citation détectée dans un texte non vide, ou si une contradiction interne est trouvée ; ne supprime jamais de contenu | Confirmé exact |
| `tmis.ai_governance.hallucination_detection.schemas.HallucinationAlert` | `dataclass` frozen : `id`, `excerpt`, `reason`, `recommendation` | Confirmé exact |
| `tmis.ai_governance.bias_detection.engine.BiasDetectionEngine` | `scan(text) -> list[BiasFinding]` : exécute chaque `BiasDetectorPort` enregistré (par défaut `GeneralizationBiasDetector`), `register()` pour en ajouter sans modifier la classe | Confirmé exact |
| `tmis.ai_governance.bias_detection.ports.BiasDetectorPort` | `Protocol` : `name`, `detect(text) -> list[BiasFinding]` | Confirmé exact, aucune modification |
| `tmis.ai_governance.bias_detection.schemas.BiasFinding` | `dataclass` frozen : `id`, `detector_name`, `category`, `excerpt`, `description`, `explanation` | Confirmé exact |
| `tmis.case_intelligence.cases.ports.CaseStorePort` | `get`/`save`/`get_or_create`/`list_ids`, `Protocol` | Confirmé exact, identique aux Sprints 29/30 |
| `tmis.case_intelligence.cases.schemas.CaseProfile` | Porte `facts: list[Fact]` et `timeline_inconsistencies: list[TimelineInconsistency]` directement — exactement les deux paramètres attendus par `ConflictDetectorPort.detect()` | Confirmé exact |

Aucun de ces fichiers n'avait une forme différente de celle attendue —
aucun arbitrage utilisateur n'a donc été nécessaire avant de commencer.

## Deux écarts structurels identifiés en Phase 0, tranchés avant tout code

### 1. `AgentOutput` n'a pas de champ `case_id` — et ne doit pas en gagner un

Le prompt demande de charger le `CaseProfile` « si l'`AgentOutput` porte
de quoi retrouver un `case_id` ». `tmis.ai.schemas.agent.AgentOutput` ne
porte que `result`, `citations`, `confidence`, `warnings` — aucun
`case_id`. La contrainte « zéro changement de signature sur
`AgentInput`/`AgentOutput` » interdit d'en ajouter un.

**Décision** : réutiliser la convention déjà établie par
`SynthesisAgent` — sa citation finale porte `connector="case_store"` et
`source_id=case_profile.case_id`. `VerifierAgent._resolve_case_id()`
cherche cette citation dans `output.citations` plutôt que d'introduire un
nouveau champ. Conséquence assumée et documentée (docs/159) : la
cohérence dossier ne se déclenche jamais sur la seule sortie d'Analyse
(qui ne cite jamais le dossier, seulement le document) — uniquement une
fois la sortie de Synthèse présente dans les citations, ce que la
correction du graphe (point 2 ci-dessous) garantit.

### 2. Le graphe ne fait jamais passer la sortie de Synthesis par `verify()`

Confirmé par lecture directe de `orchestrator.py` : `graph.add_edge
("verifier", "synthesis")` puis `graph.add_edge("synthesis", END)` —
aucune arête ne ramène la sortie de `"synthesis"` vers `"verifier"`.
`VerifierAgent.verify()` n'est donc appelé que sur la sortie brute
d'Analyse, jamais sur la sortie fusionnée. C'est le bug que le prompt
demande de corriger ; le raisonnement complet sur le choix de correction
(seconde passe `verify()` plutôt que déplacement du nœud) est développé
dans le rapport d'architecture et docs/159.

## Un troisième point de vigilance, identifié en cours d'implémentation

La ligne 31 de `docs/09-roadmap-30-sprints.md` (table détaillée) mentionne
« S'appuie sur `ReasoningOrchestrator`/`ConfidenceEngine`/`ConflictDetector`
(Sprint 6) ». Le prompt de ce sprint, lui, liste explicitement et
exclusivement trois moteurs à composer (`HeuristicConflictDetector`,
`HallucinationDetectionEngine`, `BiasDetectionEngine`) et l'exige en
« composition stricte ». `ReasoningOrchestrator`
(`tmis.legal_reasoning.reasoner.orchestrator`) et `ConfidenceEngine`
(`tmis.legal_reasoning.confidence.ports`) existent bien dans le dépôt,
mais ne sont volontairement pas câblés ici : le brief du sprint est plus
récent et plus précis que la ligne de roadmap (écrite avant l'existence
de ces sprints), et ajouter ces deux moteurs aurait dépassé la portée
« composition stricte sur les 3 moteurs existants » explicitement fixée.
Documenté dans la note de révision Sprint 31 de `docs/09-roadmap-30-
sprints.md` plutôt que laissé comme un oubli silencieux.

## Conclusion

Aucun écart de forme trouvé sur les 15 fichiers désignés par le prompt —
tous ont exactement la forme attendue. Deux écarts structurels
(l'absence de `case_id` sur `AgentOutput`, l'absence d'arête retournant
vers `"verifier"` après `"synthesis"`) ont été identifiés dès la Phase 0,
tranchés avant tout code et documentés ci-dessus, dans le rapport
d'architecture et dans docs/159-architecture-agent-verificateur.md — pas
appliqués silencieusement.
