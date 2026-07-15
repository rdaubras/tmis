# Rapport d'audit — Sprint 35 (Agent Contrats, réel)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« PHASE 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), ce qui
existe déjà pour chacun des fichiers désignés par le prompt, confirme
qu'aucun n'a changé de forme depuis son sprint d'origine, et tranche les
deux questions ouvertes explicitement posées par la mission.

## Fichiers désignés par le prompt : forme confirmée, aucun écart de contenu

| Fichier | Ce qu'il fournit déjà | Confirmation |
|---|---|---|
| `tmis.agents.contract_agent.ContractAgent` | Placeholder Sprint 1 : `name = "contract"`, `async def run(agent_input) -> AgentOutput: raise NotImplementedError(...)` | Confirmé exact — remplacé par ce sprint |
| `tmis.agents.orchestrator.Orchestrator` | Graphe LangGraph `analysis -> verifier -> synthesis -> verifier_final -> END` ; docstring documentant le patron pour un agent futur — aucun agent au-delà de `analysis`/`verifier`/`synthesis` n'y est câblé | Confirmé exact — **non modifié** ; ce sprint ne demande pas de nœud `"contract"`, et ni `ResearchAgent` ni `JurisprudenceAgent` n'y ont jamais été ajoutés (même précédent que Sprint 34) |
| `tmis.agents.contracts` | Ré-export de `AgentInput`/`AgentOutput`/`AgentPort`/`ConfidenceLevel` depuis `tmis.ai.schemas.agent` | Confirmé exact, aucune modification |
| `tmis.agents.bootstrap` | `get_research_agent()`, `get_jurisprudence_agent()` : `@lru_cache`, composition-root | Confirmé exact — patron réutilisé pour `get_contract_agent()` |
| `tmis.agents.citations` | `research_citation_to_citation(result, citation) -> Citation`, utilisé par `ResearchAgent`/`JurisprudenceAgent` | Confirmé exact — **non pertinent pour ce sprint** (`ContractAgent` ne consomme pas de `ResearchResult`/`ResearchCitation`, aucune raison de l'importer) |
| `tmis.agents.analysis_agent.AnalysisAgent` (patron de référence Sprint 29) | Constructeur `kernel`/`document_store`/`case_store`/`fabric`/`governance`/`firm_id`, tous optionnels ; `AIIntelligenceFabric.route(RoutingRequest(firm_id, task_type, prompt))` pour choisir le modèle d'un appel `TMISKernel.complete(prompt, provider=...)` ; `AIGovernancePlatform.explainability.generate()` optionnel ; lecture `DocumentStorePort`/`CaseStorePort` | Confirmé exact — patron de câblage Fabric/Kernel/Governance/ports réutilisé à l'identique |
| `tmis.agents.jurisprudence_agent.JurisprudenceAgent` (patron de référence le plus récent) | Combine délégation à un port existant (recherche) et câblage Fabric/Kernel (comparaison générative) sur le même agent | Confirmé exact — précédent direct pour combiner deux patrons sur `ContractAgent` (lecture de document + confrontation à `ClauseEngine` + synthèse générative) |
| `tmis.cabinet_knowledge.clauses.engine.ClauseEngine` | `search(firm_id, domain=None, clause_type=None, keyword=None) -> list[Clause]`, seule méthode de lecture en masse ; `create_clause`/`get_clause`/`add_variant` gèrent l'écriture, non utilisées par un agent de lecture | Confirmé exact — signature exacte annoncée par le prompt, utilisée telle quelle, aucun contournement via `KnowledgeSpace` directement |
| `tmis.cabinet_knowledge.clauses.schemas.{Clause, ClauseVariant}` | `Clause` : `id`, `domain`, `clause_type`, `title`, `variants: tuple[ClauseVariant, ...]`, `comments`, `jurisprudence_refs` ; `ClauseVariant` : `id`, `text`, `notes`, `language` | Confirmé exact, aucune modification |
| `tmis.cabinet_knowledge.templates.engine.CabinetTemplateEngine` | `list_templates(firm_id, document_type: DocumentType \| None) -> list[CabinetTemplate]` ; `CabinetTemplate.structure: tuple[str, ...]` indexée par `DocumentType` (Sprint 7) | Confirmé exact — **écart structurel identifié** : aucune valeur de `DocumentType` ne représente un contrat (voir plus bas) |
| `tmis.cabinet_knowledge.templates.schemas.CabinetTemplate` | `document_type: DocumentType`, `structure: tuple[str, ...]` | Confirmé exact, aucune modification |
| `tmis.document_intelligence.schemas.record.DocumentRecord` | `ocr_text: str`, `raw_bytes: bytes`, `entities`, `timeline_events`, `warnings`, `status: ProcessingStatus` | Confirmé exact — `ocr_text` utilisé, `raw_bytes` jamais relu |
| `tmis.document_intelligence.storage.ports.DocumentStorePort` / `.in_memory_store.InMemoryDocumentStore` | `save`/`get`/`list_ids`, implémentation process-locale par `dict` | Confirmé exact, même port que `AnalysisAgent` |
| `tmis.legal_drafting.versioning.service.InMemoryVersioningService` | `compare(document_id, version_a: int, version_b: int) -> VersionDiff`, calculé sur `DocumentVersion.sections: tuple[Section, ...]` stockées par `snapshot()` | Confirmé exact — **opère sur le modèle `Section`/`Paragraph` du Legal Drafting Studio pour un même `document_id`, pas sur deux `DocumentRecord` uploadés séparément** (voir Question Ouverte n°1 ci-dessous) |
| `tmis.legal_drafting.versioning.ports.VersioningPort` | `snapshot`/`list_versions`/`get`/`compare`/`restore`, tous paramétrés par `document_id: str` + `version_number: int`, jamais par un second `document_id` | Confirmé exact, aucune modification |
| `tmis.legal_drafting.versioning.schemas.{DocumentVersion, VersionDiff}` | `DocumentVersion.sections: tuple[Section, ...]` ; `VersionDiff.{added,removed,changed}_paragraph_ids: tuple[str, ...]`, identifiants de `Paragraph.id` (stable, attribué par le Studio) | Confirmé exact — aucun champ ne référence un second `document_id` ; le modèle ne couvre que des snapshots successifs du même document |
| `tmis.legal_copilot_framework.copilots.contrats` | `build(deps) -> LegalCopilot` : déclare un `CopilotSpec` de démonstration avec son propre `PromptRegistry` (`deps.prompt_registry.register("contrats-system", ...)`), domaine `LegalDomain.COMMERCIAL` (`tmis.ai_team.capabilities.schemas.LegalDomain`), docstring explicite « Demonstrates the architecture, not full contract-law logic » | Confirmé exact — lu, **non câblé** sur `ContractAgent` : un second mécanisme de prompting pour la même responsabilité aurait été introduit sinon |
| `tmis.ai_fabric.fabric.AIIntelligenceFabric` | `route(RoutingRequest) -> RoutingDecision` — `RoutingDecision.model` porte `name` et `provider` | Confirmé exact, aucune modification |
| `tmis.ai.kernel.kernel.TMISKernel.complete` | `complete(prompt, *, provider=None, use_cache=True) -> ModelResponse` — seul point d'appel à un provider | Confirmé exact, aucune modification |
| `tmis.ai_governance.overview.AIGovernancePlatform` | `explainability.generate(firm_id, production_id, *, summary, steps_followed, agents_involved=(), models_used=(), documents_consulted=())` | Confirmé exact, aucune modification |

Aucun de ces fichiers n'avait un contenu différent de celui attendu. Deux
questions structurantes, explicitement posées par le prompt ou découvertes
en cours de lecture, ont été tranchées avant tout code.

## Question Ouverte n°1 (posée par le prompt) : la comparaison de version peut-elle réutiliser `VersioningPort` ?

**Non.** La lecture directe de `InMemoryVersioningService.compare()`
confirme que ses deux paramètres `version_a`/`version_b` sont des
`version_number: int` d'un **même** `document_id`, résolus contre un
historique de `DocumentVersion` construit exclusivement par
`snapshot(document_id, sections, author)` — c'est-à-dire par le flux
d'édition du Legal Drafting Studio, jamais par un upload de document. La
granularité de `VersionDiff` (`added/removed/changed_paragraph_ids`)
repose sur `Paragraph.id`, un identifiant stable attribué par le Studio à
la création du paragraphe — un `DocumentRecord.ocr_text` uploadé n'a
aucun équivalent.

Un contrat de ce sprint est deux fichiers distincts, avec deux
`document_id` différents et un texte brut sans `Paragraph.id`. Appeler
`VersioningPort.compare()` dessus n'a pas de sens vis-à-vis de sa propre
signature (elle ne prend même pas de second `document_id` en paramètre) —
il n'y a littéralement rien à passer à `version_a`/`version_b` pour deux
contrats uploadés séparément.

**Décision** : implémentation d'un type minimal local,
`ContractVersionDiff` (dans `tmis/agents/contract_agent.py`, pas un
module partagé — un seul appelant), calculé par
`difflib.SequenceMatcher` (bibliothèque standard) sur des paragraphes de
texte brut. Ni un second moteur de versioning (aucun `snapshot()`, aucun
stockage, calcul stateless à la demande), ni une extension de
`VersioningPort` — voir docs/163-architecture-agent-contrats.md pour le
détail complet du raisonnement.

## Question Ouverte n°2 (découverte en Phase 0, non posée explicitement par le prompt) : `CabinetTemplateEngine` peut-il servir aux sections manquantes ?

Le prompt demandait d'« évaluer en Phase 0 » `CabinetTemplateEngine` pour
détecter des sections manquantes dans un contrat, la retenue étant
conditionnelle (« si retenu en Phase 0 »). La lecture directe de
`tmis.legal_drafting.templates.schemas.DocumentType` montre que les neuf
valeurs de cet enum sont `CONSULTATION`, `NOTE_INTERNE`, `COURRIER`,
`MISE_EN_DEMEURE`, `REQUETE`, `ASSIGNATION`, `CONCLUSIONS`, `MEMOIRE`,
`SYNTHESE` — **aucune ne représente un contrat**, et
`CabinetTemplateEngine.list_templates(firm_id, document_type)` ne peut
donc renvoyer aucune structure de référence pertinente pour un contrat
sans qu'un cabinet ait, par convention locale non garantie, rangé un
modèle de contrat sous l'un de ces neuf types.

**Décision** : ne pas câbler `CabinetTemplateEngine`. L'étendre (ajouter
une dixième valeur à `DocumentType`) modifierait un enum partagé conçu et
documenté pour les neuf types du Sprint 7 — exactement le type
d'extension que le prompt met en garde contre pour `VersioningPort`, pour
la même raison structurelle (le modèle ne correspond pas à ce que ce
sprint doit produire). La détection de « sections manquantes » demandée
par la mission est entièrement portée par `ClauseEngine` : un
`clause_type` connu du domaine mais absent du texte du contrat **est** la
section manquante recherchée — voir docs/163-architecture-agent-contrats.md.

## Confirmation explicite : aucun autre agent, aucune modification des ports ni des plateformes partagées

- `WatchAgent`, `DraftingAgent`, `StrategyAgent`, `CollaborationAgent` :
  **aucune ligne modifiée**.
- `ResearchAgent`, `JurisprudenceAgent` : **aucune ligne modifiée** — ce
  sprint ne touche à aucun autre agent déjà réel.
- `tmis.agents.orchestrator.Orchestrator` : **non modifié** — ni le
  graphe LangGraph, ni sa signature publique `run()`.
- `tmis.cabinet_knowledge.clauses.{engine,schemas}`,
  `tmis.cabinet_knowledge.templates.{engine,schemas}` : **aucune ligne
  modifiée** — vérifié par `git diff --stat` restreint à
  `tmis/cabinet_knowledge/`, vide.
- `tmis.legal_drafting.versioning.*` : **aucune ligne modifiée** —
  vérifié par `git diff --stat` restreint à `tmis/legal_drafting/`, vide.
- `tmis.ai.kernel.kernel.TMISKernel`, `tmis.ai_fabric.fabric.
  AIIntelligenceFabric`, `tmis.ai_governance.overview.
  AIGovernancePlatform` : **aucune ligne modifiée**.
- `tmis.legal_copilot_framework.copilots.contrats` : **aucune ligne
  modifiée** — lu, non câblé, comme documenté ci-dessus.
- `AgentInput`/`AgentOutput`/`AgentPort`/`ClauseEngine.search()`/
  `CabinetTemplateEngine`/`DocumentRecord` : **zéro changement de
  signature**.

## Composants réutilisés tels quels / étendus / réellement nouveaux

| Composant | Statut | Détail |
|---|---|---|
| `DocumentStorePort`/`InMemoryDocumentStore` (Sprint 26) | Réutilisé tel quel | Même port, même défaut que `AnalysisAgent` ; `ocr_text` lu, `raw_bytes` jamais re-parsé |
| `CaseStorePort`/`InMemoryCaseStore`/`CaseProfile` (Sprint 26) | Réutilisé tel quel | Même port que `AnalysisAgent`/`JurisprudenceAgent` |
| `ClauseEngine.search(firm_id, domain)` (Sprint 12) | Réutilisé tel quel | Seul point d'accès à la bibliothèque de clauses, appelé une fois par exécution, aucun contournement via `KnowledgeSpace` |
| `AIIntelligenceFabric.route()` (Sprint 14) | Réutilisé tel quel | `task_type="contract_risk_synthesis"`, nouveau uniquement comme valeur de chaîne libre |
| `TMISKernel.complete()` (Sprint 2) | Réutilisé tel quel | Seul point d'appel génératif |
| `AIGovernancePlatform.explainability` (Sprint 15) | Réutilisé tel quel | Même patron `generate()` que les trois agents précédents |
| `tmis.agents.bootstrap` (composition root) | Étendu | Ajout de `get_contract_agent()`, aucune fonction existante modifiée |
| `ContractAgent._detect_clause_risks`/`_match_variant`/`_overlap_score` | Réellement nouveau | Confrontation clause-par-clause du contrat à la bibliothèque, absente ailleurs dans le dépôt |
| `ContractVersionDiff`/`_diff_contract_paragraphs` | Réellement nouveau | Type et calcul locaux, scopés à `ContractAgent`, sur `difflib` (bibliothèque standard) — pas un second moteur de versioning |
| `ContractAgent._generate_synthesis`/`_build_prompt` | Réellement nouveau | Synthèse générative de risques, absente ailleurs (le copilote de démonstration Sprint 24 ne la produit pas) |
| `CabinetTemplateEngine` | Non retenu (évalué, écarté) | Aucune valeur de `DocumentType` ne représente un contrat — voir Question Ouverte n°2 |

## Conclusion

Aucun des fichiers désignés par le prompt n'avait un contenu différent de
celui attendu. Les deux questions structurantes de ce sprint — la
réutilisabilité de `VersioningPort` et celle de `CabinetTemplateEngine` —
ont toutes deux été tranchées par la négative, pour la même raison de
fond (un modèle de données conçu pour un usage différent), et
documentées ici ainsi que dans le rapport d'architecture et
docs/163-architecture-agent-contrats.md, jamais appliquées
silencieusement.
