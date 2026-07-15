# Rapport d'architecture — Sprint 35 (Agent Contrats, réel)

## Résumé

Le Sprint 35 relie `ContractAgent` (placeholder depuis le Sprint 1) aux
plateformes déjà livrées, en suivant le patron de câblage établi par
`AnalysisAgent` (Sprint 29) pour la partie génération/synthèse : lecture
d'un `DocumentRecord` réellement persisté, câblage
`AIIntelligenceFabric.route()` → `TMISKernel.complete()` pour une
synthèse générative, `AIGovernancePlatform.explainability` optionnel. Le
travail réellement nouveau — confirmé absent ailleurs dans le dépôt par
la Phase 0 (`docs/reports/sprint-35-rapport-audit.md`) — est la
confrontation du texte d'un contrat uploadé à la bibliothèque de clauses
du cabinet (`ClauseEngine.search()`, Sprint 12) pour détecter les clauses
à risque et les clauses manquantes, et une comparaison de version minimale
entre deux contrats uploadés quand demandée.

Périmètre livré : `tmis/agents/contract_agent.py` (réécrit, placeholder
-> implémentation réelle), `tmis/agents/bootstrap.py` (ajout de
`get_contract_agent()`), 14 tests unitaires + 2 tests d'intégration
nouveaux, 0 test existant modifié, docs/163-architecture-agent-contrats.md,
note de révision dans docs/09-roadmap-30-sprints.md.

**Aucun autre agent de `tmis.agents` touché. `ClauseEngine`,
`CabinetTemplateEngine`, `VersioningPort`, `AIIntelligenceFabric`,
`TMISKernel`, `AIGovernancePlatform` non modifiés. `Orchestrator`
(LangGraph) non modifié. Zéro changement de signature sur
`AgentInput`/`AgentOutput`/`AgentPort`/`ClauseEngine.search()`/
`CabinetTemplateEngine`/`DocumentRecord`.**

## Décisions structurantes

### La confrontation aux clauses est un usage en lecture seule de `ClauseEngine.search()` — aucune bibliothèque concurrente

La mission impose explicitement que tout accès à la bibliothèque de
clauses passe par `ClauseEngine.search(firm_id, domain, clause_type,
keyword)`. `ContractAgent` appelle cette méthode **une seule fois** par
exécution, sans filtre `clause_type`/`keyword`, pour récupérer toute la
bibliothèque du domaine résolu (`agent_input.context["domain"]`, défaut
`LegalDomain.COMMERCIAL`) :

```python
clauses = self._clause_engine.search(self._firm_id, domain=domain)
findings = self._detect_clause_risks(document, clauses)
```

C'est ensuite `ContractAgent`, pas `ClauseEngine`, qui confronte chaque
`Clause` retournée au texte du contrat — la logique de confrontation
(présence, variante la plus proche, indicateur de risque) est neuve, mais
elle ne lit et n'écrit jamais rien dans `KnowledgeSpace` directement :
tout passe par l'unique méthode publique de lecture en masse de
`ClauseEngine`.

### Détection de risque : recouvrement de mots, pas un second moteur sémantique

Pour choisir la variante la plus proche du texte du contrat parmi
`clause.variants`, `_overlap_score()` compte les mots significatifs
(longueur > 3) de `variant.text` présents dans `document.ocr_text` — un
recouvrement lexical explicite, dans le même esprit que
`KeywordOverlapReranker` (Sprint 2/28), déjà présent dans le dépôt pour un
besoin comparable (comparer un texte à une référence sans modèle
d'embedding dédié). Une clause est reportée à risque dans deux cas :

1. Les notes de la variante la plus proche (`ClauseVariant.notes`, écrites
   par le cabinet lui-même en créant la clause) contiennent un indicateur
   de risque explicite (« risque », « défavorable », « déséquilibr[é] »,
   « abusif », etc.) ;
2. Le recouvrement avec la variante la plus proche reste faible (< 30 %
   des mots significatifs) malgré la présence détectée de la clause —
   signe d'une formulation non standard.

Une clause dont le `clause_type`/`title` n'apparaît pas du tout dans le
texte est reportée `status: "missing"` — c'est ce mécanisme, et non
`CabinetTemplateEngine`, qui porte la détection de « sections
manquantes » demandée par la mission (voir plus bas pourquoi).

### `CabinetTemplateEngine` évalué, non retenu — aucune valeur de `DocumentType` ne représente un contrat

La mission conditionnait explicitement le câblage de
`CabinetTemplateEngine` à ce que la Phase 0 le retienne (« si retenu en
Phase 0 »). La lecture directe de
`tmis.legal_drafting.templates.schemas.DocumentType` (neuf valeurs :
`CONSULTATION`, `NOTE_INTERNE`, `COURRIER`, `MISE_EN_DEMEURE`, `REQUETE`,
`ASSIGNATION`, `CONCLUSIONS`, `MEMOIRE`, `SYNTHESE`) confirme qu'aucune
ne représente un contrat — `CabinetTemplateEngine.list_templates(firm_id,
document_type)` ne peut donc renvoyer aucune structure pertinente pour un
contrat sans un rangement conventionnel non garanti par un cabinet.

**Décision** : ne pas câbler `CabinetTemplateEngine`. L'alternative
(ajouter une dixième valeur à `DocumentType`) étendrait un enum partagé
conçu pour les neuf types du Sprint 7 à un usage qu'il n'a jamais eu
vocation à couvrir — exactement le raisonnement que la mission applique
déjà à `VersioningPort` (voir ci-dessous), appliqué ici par symétrie à la
même classe de problème. `ClauseEngine` seul porte la responsabilité des
« sections manquantes », sans avoir besoin d'un second mécanisme ni d'une
extension de schéma partagé. Voir
docs/163-architecture-agent-contrats.md pour le détail complet.

### Comparaison de version : question ouverte tranchée — type minimal local, pas une extension de `VersioningPort`

La mission posait explicitement la question et exigeait qu'elle soit
tranchée en Phase 0 plutôt que devinée pendant l'implémentation. La
lecture directe de `InMemoryVersioningService.compare(document_id,
version_a: int, version_b: int)` confirme qu'elle opère sur des
`version_number` d'un **même** `document_id`, résolus contre un historique
de `DocumentVersion` (`sections: tuple[Section, ...]`) construit
exclusivement par `snapshot()` — le flux d'édition du Legal Drafting
Studio, jamais un upload de contrat. `VersionDiff` compare à la
granularité de `Paragraph.id`, un identifiant stable attribué par le
Studio — un `DocumentRecord.ocr_text` uploadé n'en a pas l'équivalent.
Un contrat de ce sprint est deux fichiers distincts (deux `document_id`),
pas deux versions du même document du Studio : la signature même de
`compare()` ne prend pas de second `document_id` en paramètre, il n'y a
donc rien à lui passer pour ce cas d'usage.

**Décision** : `ContractVersionDiff` (frozen dataclass locale à
`tmis/agents/contract_agent.py`, un seul appelant, pas un module
partagé), calculée par `difflib.SequenceMatcher` (bibliothèque standard
Python) sur les paragraphes de texte brut des deux `DocumentRecord.
ocr_text` (`text.split("\n\n")`) :

```python
def _diff_contract_paragraphs(text_a: str, text_b: str) -> ContractVersionDiff:
    paragraphs_a = _split_paragraphs(text_a)
    paragraphs_b = _split_paragraphs(text_b)
    matcher = difflib.SequenceMatcher(None, paragraphs_a, paragraphs_b)
    ...  # added / removed / changed via get_opcodes()
```

Ce diff n'est produit que si `agent_input.context["compare_document_id"]`
résout à un second `DocumentRecord` réellement persisté ; sans second
document, `result["version_diff"]` vaut `None`. Ni un second moteur de
versioning (aucun stockage, aucun `snapshot()`, calcul stateless à la
demande) ni une extension de `VersioningPort` à un modèle de document
qu'il n'a jamais eu vocation à couvrir — exactement l'alternative que la
mission demandait d'éviter. Vérifié par test
(`test_contract_agent_compares_two_documents_when_asked`,
`test_two_persisted_contract_versions_produce_a_paragraph_diff`).

### La synthèse générative suit le patron `AnalysisAgent`/`JurisprudenceAgent` — un seul appel `TMISKernel.complete()`, jamais deux

```python
async def _generate_synthesis(
    self, document, case_profile, findings, version_diff
) -> tuple[str, str]:
    prompt = self._build_prompt(document, case_profile, findings, version_diff)
    model_name, provider_name = self._route_model(prompt)
    response = await self._kernel.complete(prompt, provider=provider_name)
    return model_name, response.text
```

`_route_model()` reproduit exactement `AnalysisAgent._route_model()`/
`JurisprudenceAgent._route_model()` : `RoutingRequest(firm_id,
"contract_risk_synthesis", prompt)` (un `task_type` propre à ce sprint,
chaîne libre non contrainte par une énumération) puis `self._kernel.
complete(prompt, provider=decision.model.provider)`. Sans `fabric`
injecté (paramètre optionnel), le routage retombe sur `"default", None`.
Contrairement à `JurisprudenceAgent` (qui saute la génération sur zéro
résultat), `ContractAgent` génère toujours une synthèse dès qu'un
document existe — même choix qu'`AnalysisAgent`, cohérent avec le fait
qu'un contrat sans clause à risque ni clause manquante reste un résultat
à synthétiser (« ce contrat est conforme aux standards du cabinet »),
pas un cas vide. Vérifié par test
(`test_contract_agent_generates_a_synthesis_without_a_fabric`,
`test_contract_agent_routes_synthesis_through_the_fabric`).

`ContractAgent` n'importe ni ne câble
`legal_copilot_framework.copilots.contrats.build()` ni son
`PromptRegistry` : lu en Phase 0, confirmé être une démonstration
indépendante (son propre docstring : « Demonstrates the architecture, not
full contract-law logic »), un second mécanisme de prompting pour la même
responsabilité aurait été introduit sinon — explicitement interdit par la
mission.

### `CaseStorePort` injecté pour le contexte du dossier — optionnel, comme pour les trois agents précédents

Même patron qu'`AnalysisAgent`/`JurisprudenceAgent` : `CaseStorePort.
get(case_id)` si `agent_input.case_id` est fourni (défaut
`InMemoryCaseStore()`), titre et nombre d'acteurs injectés dans le prompt
de synthèse. Un `case_id` fourni mais introuvable ne bloque jamais
l'analyse — avertissement explicite (`"Case {case_id} was not found in
the case store."`), même formulation que les deux agents précédents.
Vérifié par test
(`test_contract_agent_uses_case_profile_when_case_id_is_known`,
`test_contract_agent_warns_when_case_id_not_found`).

### Confiance et explicabilité

```python
@staticmethod
def _confidence_for(clauses: list[Clause], warnings: list[str]) -> ConfidenceLevel:
    if not clauses:
        return ConfidenceLevel.LOW
    if warnings:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.HIGH
```

Même structure que `AnalysisAgent._confidence_for` : une bibliothèque de
clauses vide pour le domaine résolu (rien de fiable à confronter) dégrade
à `LOW`, tout avertissement (dossier introuvable, document de comparaison
introuvable, avertissements portés par le `DocumentRecord` lui-même)
dégrade à `MEDIUM`, sinon `HIGH` — la confiance reflète la fiabilité de la
confrontation à la bibliothèque, pas le nombre de clauses à risque
trouvées. `_record_explainability()` reprend le patron des trois agents
précédents (`steps_followed` détaillés, `models_used`, `documents_
consulted` incluant le second document si comparé) — optionnel
(`governance: AIGovernancePlatform | None = None`).

### `ContractAgent` n'est câblé ni dans l'`Orchestrator` ni dans le chat

Même choix que `JurisprudenceAgent` au Sprint 34, pour la même raison :
ni `ResearchAgent` ni `JurisprudenceAgent` — les deux patrons de référence
explicites de ce sprint — n'ont jamais été ajoutés au graphe LangGraph de
l'`Orchestrator`, ni exposés dans un mode dédié du chat ; ils restent
exposés uniquement via `tmis.agents.bootstrap.get_*_agent()`. Étendre
l'un ou l'autre à `ContractAgent` aurait établi un précédent qu'aucun des
deux patrons de référence ne suit lui-même, sans qu'aucune partie de la
mission ne le demande explicitement — documenté comme scope futur dans
docs/163-architecture-agent-contrats.md plutôt qu'improvisé.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `ContractAgent` (lecture) | `DocumentStorePort.get()`/`CaseStorePort.get()` (Sprint 26, inchangés) | Un second parseur de `raw_bytes`, un second store de dossiers |
| `ContractAgent._detect_clause_risks`/`_match_variant` | `ClauseEngine.search(firm_id, domain)` (Sprint 12, inchangé) | Une seconde bibliothèque de clauses, un second point d'accès à `KnowledgeSpace` |
| `ContractVersionDiff`/`_diff_contract_paragraphs` | `difflib.SequenceMatcher` (bibliothèque standard) | Un second moteur de versioning, une extension de `VersioningPort` |
| `ContractAgent._generate_synthesis` | `AIIntelligenceFabric.route()` (Sprint 14), `TMISKernel.complete()` (Sprint 2) | Un second client LLM, un second routeur de modèle, `legal_copilot_framework.PromptRegistry` |
| `ContractAgent._record_explainability` | `AIGovernancePlatform.explainability.generate()` (Sprint 15) | Une gouvernance de production parallèle |
| `tmis.agents.bootstrap.get_contract_agent` | `get_kernel()` (Sprint 2), `get_ai_intelligence_fabric()` (Sprint 14), `get_case_intelligence_workflow().case_store` (Sprint 4), `get_clause_engine()` (Sprint 12), `get_ai_governance_platform()` (Sprint 15) — même patron `@lru_cache` que `get_jurisprudence_agent()` | Un second singleton de Kernel, de Fabric, de `ClauseEngine` ou de plateforme de gouvernance |

## Aucun test existant modifié

`ContractAgent` était un placeholder qui levait `NotImplementedError` —
aucun test préexistant ne l'exerçait au-delà de vérifier cette exception
(si un tel test existait, il aurait échoué à la compilation de ce sprint ;
`git diff --stat` sur `tests/` en dehors des deux nouveaux fichiers est
vide, confirmant qu'aucun test préexistant ne dépendait du comportement
placeholder).

16 tests nouveaux :

- `tests/unit/agents/test_contract_agent.py` (+14, nouveau fichier) :
  absence de `document_id` -> `LOW`, document introuvable -> `LOW`,
  détection clause à risque/manquante/standard via un `ClauseEngine` de
  test, résolution du domaine depuis le contexte, bibliothèque vide ->
  `LOW`, synthèse générée sans/avec `fabric` injecté, dossier
  connu/introuvable, comparaison de deux documents (diff ajouté/
  supprimé/modifié), document de comparaison introuvable, explicabilité
  enregistrée.
- `tests/integration/agents/test_contract_agent_integration.py` (+2,
  nouveau fichier) : bout en bout sur un vrai `ClauseEngine` (vraie
  `KnowledgeSpace`/`InMemoryKnowledgeStore`, clauses réellement créées via
  `create_clause()`), vrai `DocumentStorePort`, vrai `TMISKernel.
  complete()`, vrai `AIGovernancePlatform` ; second test bout en bout sur
  deux contrats réellement persistés produisant un diff de paragraphe
  réel.

## Vérification finale

- `pytest -q` (depuis `backend/`) → **2167 passed, 7 skipped** (2153
  tests préexistants + 14 nouveaux, 0 régression ; les 7 `skipped` sont
  préexistants, gatés par `TMIS_REDIS_URL`/
  `TMIS_RUN_MODEL_DOWNLOAD_TESTS`, non liés à ce sprint).
- `ruff check src tests` (commande CI) → **All checks passed** (quelques
  dépassements de longueur de ligne dans `contract_agent.py` et dans le
  test unitaire, détectés et corrigés avant ce résultat final).
- `mypy src` (commande CI, mode strict) → **Success: no issues found in
  1896 source files**.
- Confirmation explicite de périmètre : `git diff --stat` sur
  `tmis/agents/` ne montre que `contract_agent.py` (réécrit) et
  `bootstrap.py` (ajout de `get_contract_agent()`). `git diff --stat` sur
  `tmis/cabinet_knowledge/`, `tmis/legal_drafting/`,
  `tmis/agents/orchestrator.py`, `tmis/ai_fabric/`, `tmis/ai/kernel/`,
  `tmis/ai_governance/`, `tmis/legal_copilot_framework/` est vide.
