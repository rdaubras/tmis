# Rapport d'architecture — Sprint 43 (Consolidation de dette technique)

## Résumé

Sprint de plomberie interne, même famille que les Sprints 10, 21, 22, 37
et 42 : zéro nouvelle fonctionnalité métier, zéro nouveau module, zéro
rupture de compatibilité. Quatre livrables de code/docs, détaillés
ci-dessous ; le cinquième point du brief (marketplace) reste un audit
pur, sans code, voir `docs/171-audit-marketplace.md`.

1. **`tests/contracts/`** : nouvelle suite de 4 fichiers / 18 tests,
   indépendante des tests unitaires par module, couvrant `AgentInput`/
   `AgentOutput`, `Citation`/`ResearchCitation`, `KnowledgeRelation`, et
   la permission RBAC `COPILOT_MANAGE`.
2. **`case_intelligence`** : `get_case_store()` (singleton `@lru_cache`,
   `SQLAlchemyCaseStore`) injecté dans `get_case_intelligence_workflow()`
   et dans `core.tasks.case_tasks.trigger_case_workflow_task`, remplaçant
   le défaut implicite `InMemoryCaseStore` des endpoints synchrones
   `/api/v1/cases/*`.
3. **`docs/151-architecture-persistance.md`** mis à jour (limite résolue).
4. **`docs/reports/sprint-43-rapport-audit.md`** (Phase 0, y compris la
   correction de la prémisse `COPILOT_MANAGE` tranchée avec
   l'utilisateur avant tout code).
5. **`docs/171-audit-marketplace.md`** + **`docs/CHANGELOG-roadmap.md`**
   (extraction depuis `docs/09-roadmap-30-sprints.md`).

**Aucune route API existante n'a changé de forme. Aucun port
(`CaseStorePort`, `CaseIntelligenceWorkflow.__init__`) n'a changé de
signature — seul le comportement *par défaut* des composition roots
change.**

## Décision structurante : `get_case_store()`, même patron que Sprint 37

```python
# case_intelligence/bootstrap.py
@lru_cache
def get_case_store() -> CaseStorePort:
    return SQLAlchemyCaseStore()


@lru_cache
def get_case_intelligence_workflow() -> CaseIntelligenceWorkflow:
    kernel = get_kernel()
    pipeline = get_document_pipeline()
    return CaseIntelligenceWorkflow(
        case_store=get_case_store(),
        document_store=pipeline.document_store,
        event_bus=kernel.event_bus,
        summary_generator=CaseSummaryGenerator(kernel),
    )
```

Exactement le patron `document_intelligence.bootstrap.
get_document_store()` du Sprint 37 : un singleton `@lru_cache` qui
construit toujours l'implémentation de production (`SQLAlchemyCaseStore`
lit `Settings.database_url` directement, pas de branche réel/fixture à ce
niveau), injecté dans tous les composition roots qui retombaient
implicitement sur le défaut du port.

`core.tasks.case_tasks.trigger_case_workflow_task` (le chemin Celery)
appelait déjà `SQLAlchemyCaseStore()` — la bonne implémentation, mais une
nouvelle instance à chaque tâche plutôt que le singleton partagé. Corrigé
en appelant `get_case_store()` à la place :

```python
workflow = CaseIntelligenceWorkflow(
    case_store=get_case_store(),
    document_store=document_store,
    auto_subscribe=False,
)
```

`document_store` reste construit directement (`SQLAlchemyDocumentStore()`
par tâche) — pattern déjà établi et documenté au Sprint 37 comme
l'exception volontaire, non touché ici puisque hors périmètre de ce
sprint.

`CaseIntelligenceWorkflow.__init__` garde `case_store: CaseStorePort |
None = None` inchangé — les tests qui injectent explicitement
`InMemoryCaseStore()` (la majorité des tests unitaires par agent)
continuent de fonctionner sans aucun changement.

## Conséquence sur les tests d'intégration existants

Comme au Sprint 37, remplacer un défaut en mémoire par un store
Postgres réel révèle les tests qui dépendaient implicitement de l'ancien
comportement — sauf qu'ici l'ampleur est plus grande : `workflow.
case_store` est désormais lu/écrit par de nombreux tests d'intégration
inter-contextes (chat, legal_reasoning, legal_drafting), pas seulement
par `case_intelligence` lui-même. Suite pytest complète lancée
immédiatement après le changement de câblage (avant tout ajout de test) :
**25 échecs**, tous dans des tests qui appelaient
`get_case_intelligence_workflow().case_store.get_or_create(...)`/`.save(
...)`/`.get(...)` sans jamais lier `SessionLocal` à une base de données
joignable (aucun Postgres n'est joignable dans cet environnement, voir
`docs/reports/sprint-43-rapport-audit.md` §3).

Un cas plus subtil, à part les échecs de connexion : `test_
create_draft_reaches_every_upstream_engine_end_to_end`
(`test_drafting_orchestrator_integration.py`) échouait avec une
assertion incorrecte (`fact_ids == ('7a3d6d09-...', 'fact-1')` au lieu de
`('fact-1',)`), pas avec une erreur de connexion — parce qu'en l'absence
de fixture SQLite propre, ce fichier héritait silencieusement du bind
`SessionLocal` laissé par le fichier de test précédent dans l'ordre de
collecte pytest (le sessionmaker `SessionLocal` est un singleton
mutable process-wide, `.configure(bind=...)` n'est jamais réinitialisé
entre fichiers de test). Ce risque d'ordre de collecte est corrigé
partout, pas seulement pour ce fichier — chaque fichier qui touche
`workflow.case_store` obtient désormais sa propre base SQLite jetable
(`tmp_path`), au même patron déjà établi par `test_case_api.py`/`test_
document_upload_api.py` (Sprint 26/37).

**Fichiers de test adaptés (fixture de câblage uniquement, aucune
assertion métier changée)** :

| Fichier | Changement |
|---|---|
| `tests/integration/case_intelligence/test_case_api.py` | `case_profiles` ajoutée à la liste de tables `create_all` existante ; `get_case_store.cache_clear()` ajouté |
| `tests/integration/case_intelligence/test_case_analysis_api.py` | idem |
| `tests/integration/ai/test_chat_api_integration.py` | Nouvelle fixture `autouse` (base SQLite dédiée) — le fichier n'avait auparavant aucune isolation base de données |
| `tests/integration/legal_reasoning/test_reasoning_orchestrator_integration.py` | idem |
| `tests/integration/legal_drafting/test_drafting_orchestrator_integration.py` | idem |

`tests/integration/legal_reasoning/test_reasoning_api_integration.py` et
`tests/integration/legal_drafting/test_drafting_api_integration.py`
n'ont pas eu besoin de changement : ils n'appellent jamais
`workflow.case_store.*` directement (seulement `.cache_clear()` sur le
singleton), et aucun de leurs scénarios ne fait transiter un `case_id`
réel jusqu'au store. `tests/integration/document_intelligence/
test_document_analysis_api.py` avait déjà un `create_all(sync_engine)`
sans filtre de table (toutes les tables enregistrées, dont
`case_profiles`) — non touché.

Vérification de non-dépendance à l'ordre de collecte : sous-ensemble des
5 fichiers modifiés relancé en ordre inverse de fichiers → 43 passed,
même résultat qu'en ordre normal.

## `tests/contracts/` : conception

Quatre fichiers, chacun construisant son type depuis un point de
production réel plutôt que depuis une fixture à la main, conformément à
la consigne du brief. Aucun framework de contract testing externe (type
Pact) introduit — tests Pydantic/dataclass/pytest natifs, cohérents avec
le reste du dépôt.

- **`test_agent_input_contract.py`** (9 tests) — construit `AgentInput`
  via `api.v1.chat.routes._agent_input()` à partir d'un `ChatMessageRequest`
  avec un `case_id` non-UUID (`"case-contract-1"`), puis fait transiter
  cette même instance à travers `AnalysisAgent`, `SynthesisAgent`,
  `ContractAgent`, `JurisprudenceAgent`, `ResearchAgent` (paramétré) et
  `WatchAgent`, plus `BaseAgentPlugin.invoke()` avec le payload brut
  équivalent. Le premier test,
  `test_a_pre_sprint42_style_uuid_parse_would_have_raised`, reproduit
  littéralement l'expression pré-Sprint-42 (`uuid.UUID(str(case_id))`) et
  affirme qu'elle lève bien `ValueError` — la preuve regression-first que
  les tests suivants échoueraient sans la correction du Sprint 42.
- **`test_copilot_manage_permission_contract.py`** (3 tests) — reproduit
  d'abord un `RbacEngine` construit avec une matrice où `COPILOT_MANAGE`
  a été retiré de tous les rôles (`has_permission` renvoie `False`),
  confirme ensuite que `DEFAULT_ROLE_PERMISSIONS` l'accorde bien à
  `PARTNER`/`IT_ADMIN` par défaut, puis pilote le vrai endpoint `POST
  /api/v1/legal-copilots/register` via `TestClient` avec un utilisateur
  `PARTNER` réel (`RoleEngine.assign`) — bout en bout, pas seulement la
  matrice de permissions.
- **`test_citation_contract.py`** (3 tests) — utilise le vrai singleton
  `get_research_orchestrator()` (connecteurs fixtures du Sprint 2, aucun
  identifiant PISTE configuré) à travers `ResearchAgent.run()` puis
  `JurisprudenceAgent.run()`, et vérifie explicitement que
  `len(research_citations) == len(results)` — l'hypothèse d'appariement
  que `zip(..., strict=True)` suppose sans jamais la garantir à elle
  seule.
- **`test_knowledge_relation_contract.py`** (3 tests) — construit une
  `KnowledgeRelation` via `OntologyEngine.link()` et via `GraphEngine.
  link()` séparément, puis un troisième test confirme qu'une relation
  produite par `GraphEngine` reste consommable par le store de
  `OntologyEngine` (`InMemoryRelationStore.add()`) — la preuve que les
  deux producteurs partagent un seul contrat, pas deux formes
  coïncidentes.

## Résultat des tests

- `pytest -q` (depuis `backend/`) : **2251 passed, 7 skipped** (2233
  avant ce sprint, +18 nouveaux dans `tests/contracts/`, 0 régression sur
  les 2233 existants une fois les 5 fichiers de fixture adaptés).
- `ruff check src tests` → All checks passed.
- `mypy src` (`--strict`) → Success: no issues found in 1899 source
  files.

## Conclusion

`CaseStorePort` converge désormais sur `SQLAlchemyCaseStore` par défaut
sans rupture de contrat public, en suivant à l'identique le patron établi
au Sprint 37. La suite `tests/contracts/` couvre les cinq types désignés
par le brief en pilotant chacun depuis un point de production réel, avec
les deux régressions historiques (Sprint 42 `case_id`, et
`COPILOT_MANAGE` — dont la narration a été corrigée en Phase 0, voir
`docs/reports/sprint-43-rapport-audit.md` §0) reproduites puis
confirmées corrigées.
