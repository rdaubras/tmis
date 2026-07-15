# 162 — Architecture : Agent Jurisprudence (Sprint 34)

Ce document décrit le câblage réel du `JurisprudenceAgent` sur le
`ResearchOrchestrator` (Sprint 5, la LRE) pour la recherche de décisions
et sur `AIIntelligenceFabric`/`TMISKernel` (Sprint 14/2) pour la
comparaison générative — les deux patrons déjà établis, combinés pour la
première fois sur le même agent. Voir le rapport d'audit
(`docs/reports/sprint-34-rapport-audit.md`) pour le détail composant par
composant et le rapport d'architecture
(`docs/reports/sprint-34-rapport-architecture.md`) pour les décisions et
leur justification.

## Périmètre strict : un seul agent, deux patrons déjà connus

Ce sprint remplace **uniquement** le placeholder `JurisprudenceAgent` par
une implémentation réelle. **Aucun autre agent de `tmis.agents` n'est
touché** (`ContractAgent`, `WatchAgent`, `DraftingAgent`,
`StrategyAgent`, `CollaborationAgent` restent des placeholders, chacun
son propre sprint dédié — voir docs/09-roadmap-30-sprints.md). Ni
`ResearchOrchestrator` ni son pipeline interne, ni `AIIntelligenceFabric`,
ni `TMISKernel`, ni `AIGovernancePlatform` ne sont modifiés —
`JurisprudenceAgent` les appelle tels quels, comme `ResearchAgent` et
`AnalysisAgent` avant lui. `JurisprudenceAgent` n'est ni ajouté au graphe
LangGraph de l'`Orchestrator`, ni exposé dans le chat du Sprint 33 (voir
« Ce qui reste volontairement hors périmètre » ci-dessous).

## Pourquoi ce sprint combine deux patrons plutôt que d'en inventer un troisième

La mission distingue deux besoins pour cet agent :

1. **Rechercher des décisions de jurisprudence.** Ce n'est pas un besoin
   nouveau : c'est exactement ce que `ResearchOrchestrator.search()`
   fait déjà pour `ResearchAgent` (Sprint 33), à un filtre de connecteur
   près.
2. **Comparer les décisions trouvées** (convergences, divergences,
   pertinence par rapport au dossier). Ce besoin-là est réellement
   nouveau — une synthèse générative, exactement le genre de travail que
   `AnalysisAgent` (Sprint 29) fait déjà pour l'extraction de faits.

Réutiliser les deux patrons existants au lieu d'un patron sur mesure
évite une troisième façon de câbler la génération de texte, un troisième
adaptateur de citations, ou un second appel `TMISKernel.complete()` par
un chemin différent.

## Vue d'ensemble

```mermaid
flowchart TB
    Input["AgentInput\n(task_id, case_id?, context={query})"]
    Agent["JurisprudenceAgent.run()"]

    RO["ResearchOrchestrator.search(\n  query, connector_names=[\"jurisprudence\"],\n  case_id=...)\n(Sprint 5, inchangé)"]
    Conn["ConnectorManager\n(Kernel partagé)\n'jurisprudence' déjà enregistré\n(Judilibre réel ou fixture)"]
    Adapt["tmis.agents.citations.\nresearch_citation_to_citation()\n(extrait du Sprint 33, réutilisé tel quel)"]

    CaseStore["CaseStorePort\n(si case_id fourni)"]

    Fabric["AIIntelligenceFabric.route()\n(Sprint 14)"]
    Kernel["TMISKernel.complete()\n(Sprint 2 — seul point d'appel générique à un modèle)"]
    Governance["AIGovernancePlatform.explainability\n(Sprint 15)"]

    Output["AgentOutput\n(result incl. comparison, citations, confidence, warnings)"]

    Input --> Agent
    Agent -->|"search(connector_names=['jurisprudence'])"| RO
    RO --> Conn
    Agent -->|"get_citations(search_id)"| RO
    RO -->|"ResearchResult + ResearchCitation"| Adapt
    Adapt --> Agent

    Agent -->|"get(case_id) si fourni"| CaseStore --> Agent

    Agent -->|"RoutingRequest(firm_id, 'jurisprudence_comparison', prompt)"| Fabric
    Fabric -->|"RoutingDecision(model, reasons)"| Agent
    Agent -->|"complete(prompt, provider=model.provider)\n(uniquement si des résultats existent)"| Kernel
    Kernel -->|"ModelResponse.text"| Agent

    Agent -->|"explainability.generate(...)"| Governance

    Agent --> Output
```

## Recherche de décisions : un filtre de connecteur, pas un second moteur

### Découverte clé de la Phase 0 : le connecteur « jurisprudence » est déjà partagé

`tmis.ai.kernel.bootstrap.get_kernel()` construit le `ConnectorManager`
du Kernel avec :

```python
connector_manager = ConnectorManager(
    codes=build_codes_connector(),
    jurisprudence=build_jurisprudence_connector(),
    doctrine=build_doctrine_connector(),
)
```

`build_jurisprudence_connector()` (`tmis.ai.connectors.factory`) retourne
l'adaptateur Judilibre réel (`JudilibreConnector`) si les identifiants
PISTE sont configurés, sinon la fixture en mémoire
(`JurisprudenceConnector`) — mais dans les deux cas, ce connecteur est
enregistré sous la clé `"jurisprudence"` sur le `ConnectorManager` que
`get_research_orchestrator()` (`tmis.legal_research.bootstrap`) réutilise
tel quel pour construire `HybridResearchSearch(kernel,
default_connectors=kernel.connector_manager.list_connectors())`. La LRE
sait donc déjà chercher sur ce connecteur — il suffit de le lui demander
explicitement.

### `ResearchOrchestrator.search(connector_names=["jurisprudence"])`

```python
case_id = str(agent_input.case_id) if agent_input.case_id is not None else None
response = await self._orchestrator.search(
    query, connector_names=["jurisprudence"], case_id=case_id
)
```

`JurisprudenceAgent` ne connaît ni le classement, ni la déduplication, ni
le cache trois couches, ni la logique interne du connecteur : tout cela
reste entièrement dans `ResearchOrchestrator` et son pipeline (Sprint 5),
exactement comme pour `ResearchAgent`. La seule différence avec
`ResearchAgent.run()` est ce paramètre `connector_names` — déjà accepté
par la signature de `ResearchOrchestrator.search()` avant ce sprint,
aucun changement de signature nécessaire.

### L'adaptateur de citations : réutilisé, pas recopié

`ResearchAgent` (Sprint 33) définissait `_to_citation()` comme méthode
statique privée. Ce sprint l'extrait en fonction partagée
`tmis.agents.citations.research_citation_to_citation(result, citation)`
pour que `JurisprudenceAgent` appelle exactement le même code plutôt
qu'une copie :

```python
def research_citation_to_citation(result: ResearchResult, citation: ResearchCitation) -> Citation:
    return Citation(
        source_id=citation.source_id,
        connector=result.connector,
        excerpt=citation.excerpt,
        reference=citation.reference,
    )
```

`ResearchAgent` est modifié pour importer et appeler cette même fonction
au lieu de sa propre méthode — comportement identique, un seul chemin de
conversion pour les deux agents. `tmis.legal_research.citations` continue
de ne rien savoir du contrat `agents` : l'adaptateur vit dans
`tmis.agents`, comme avant.

## Comparaison de solutions jurisprudentielles : le travail réellement nouveau

### Confirmé absent ailleurs dans le dépôt (Phase 0)

Ni `legal_copilot_framework.copilots.contentieux` (qui ne fait que
lister `"agent-jurisprudence-expert"` dans un `agent_ids` de mission
type, sans logique de comparaison), ni `legal_research` (dont le rôle
s'arrête à retourner des résultats classés) ne produisent de comparaison
structurée entre décisions. Cette synthèse est donc un besoin réel de ce
sprint, pas un doublon.

### `AIIntelligenceFabric.route()` → `TMISKernel.complete()`, comme `AnalysisAgent`

```python
async def _generate_comparison(
    self, query: str, response: ResearchResponse, case_profile: CaseProfile | None
) -> tuple[str, str]:
    prompt = self._build_prompt(query, response, case_profile)
    model_name, provider_name = self._route_model(prompt)
    completion = await self._kernel.complete(prompt, provider=provider_name)
    return model_name, completion.text
```

Un seul point d'appel génératif (`TMISKernel.complete()`), routé par
`AIIntelligenceFabric.route(RoutingRequest(firm_id, "jurisprudence_comparison",
prompt))` exactement comme `AnalysisAgent` route `"document_analysis"` —
`RoutingDecision.model` porte à la fois le nom du modèle et son
`provider`, un seul appel suffit. Sans `fabric` injecté (paramètre
optionnel, comme pour `AnalysisAgent`), le routage retombe sur le
provider par défaut du Kernel plutôt que d'échouer.

### Le prompt inclut les décisions trouvées et, si disponible, le dossier

Chaque décision de `response.results` (titre, référence, date, extrait)
alimente le prompt de comparaison. Si `agent_input.case_id` est fourni et
résolu via `CaseStorePort.get(case_id)`, le titre du dossier et un
résumé chiffré (nombre d'acteurs, de faits) y sont ajoutés — pour que la
comparaison réponde aussi à « quelle pertinence pour ce dossier ? »,
demandé explicitement par la mission. `CaseStorePort` est optionnel
(défaut `InMemoryCaseStore()`, comme pour `AnalysisAgent`) : un
`case_id` absent ou introuvable ne bloque jamais la comparaison, il en
réduit simplement la portée (avertissement `"Case {case_id} was not
found in the case store."`, même patron que `AnalysisAgent`).

### Aucune génération quand il n'y a rien à comparer

Si `response.results` est vide, `_generate_comparison()` n'est jamais
appelé : comparer zéro décision n'a pas de sens, et cela évite un appel
`TMISKernel.complete()` inutile. `AgentOutput.result["comparison"]` vaut
alors `None` et un avertissement explicite est ajouté — même principe que
`ResearchAgent` pour une recherche sans résultat.

## Confiance : même formule que `ResearchAgent`

```python
@staticmethod
def _confidence_for(response: ResearchResponse) -> ConfidenceLevel:
    if not response.results:
        return ConfidenceLevel.LOW
    if response.cache_hit:
        return ConfidenceLevel.HIGH
    return ConfidenceLevel.MEDIUM
```

La confiance reflète la recherche (résultats trouvés, cache atteint ou
non), pas la qualité de la comparaison générative elle-même — cohérent
avec le fait que la comparaison peut légitimement être absente
(`None`) sans que cela dégrade `confidence` au-delà de ce que
l'absence de résultats implique déjà.

## Explicabilité

`AIGovernancePlatform.explainability.generate(...)` enregistre, pour
chaque exécution : la requête envoyée et le nombre de décisions reçues,
la lecture du dossier via `CaseStorePort` si un `case_id` a été résolu,
et le modèle utilisé pour la comparaison si une comparaison a été
générée — optionnel comme pour les trois agents précédents
(`governance: AIGovernancePlatform | None = None`).

## Ce qui reste volontairement hors périmètre

- **`Orchestrator` (graphe LangGraph)** : `JurisprudenceAgent` n'y est pas
  ajouté. `ResearchAgent` lui-même n'a jamais été câblé dans ce graphe —
  seulement exposé via `tmis.agents.bootstrap.get_research_agent()` et
  l'endpoint de chat. Étendre le graphe à la jurisprudence n'a pas été
  demandé par ce sprint et n'est pas une conséquence triviale du travail
  déjà fait ; ce reste un scope pour un sprint futur.
- **Mode `"research"` du chat (Sprint 33)** : non étendu à la
  jurisprudence. La mission l'autorisait seulement si la Phase 0
  démontrait que c'était trivial et strictement additif ; ce n'est pas le
  cas — un mode `"jurisprudence"` dédié impliquerait une convention de
  restitution UI différente (comparaison structurée en plus de résultats
  bruts), qui mérite sa propre conception plutôt qu'une improvisation
  dans ce sprint. Documenté ici comme scope futur.

## Patron de câblage disponible pour les agents suivants

`ContractAgent` (Sprint 35) et `WatchAgent` (Sprint 36) peuvent
maintenant choisir, au cas par cas, entre le patron `ResearchAgent`
(délégation pure à un port existant, aucun câblage `AIIntelligenceFabric`)
et le patron `AnalysisAgent`/`JurisprudenceAgent` (câblage
`AIIntelligenceFabric`/`TMISKernel` pour une synthèse générative) — ou,
comme ce sprint le montre, les deux à la fois quand l'agent a
légitimement besoin des deux : une recherche/lecture de données déjà
gérée ailleurs, et une synthèse générative réellement nouvelle.
