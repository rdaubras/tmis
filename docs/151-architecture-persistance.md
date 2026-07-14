# 151 — Architecture de persistance (Sprint 26)

Ce document décrit le socle de persistance ajouté au Sprint 26 derrière
les 7 ports de stockage qui, jusqu'ici, n'existaient qu'en mémoire. Voir
le rapport d'audit (`docs/reports/sprint-26-rapport-audit.md`) pour le
détail composant par composant, et le rapport d'architecture
(`docs/reports/sprint-26-rapport-architecture.md`) pour les décisions.

## Principe : composition sur les ports existants, jamais de remplacement

Aucun des 7 ports de stockage n'a changé de signature. Chaque adaptateur
SQLAlchemy implémente le port *tel quel* ; le code appelant (pipelines,
orchestrateurs, API) continue de dépendre du `Protocol`, jamais d'une
implémentation concrète — c'est ce qui permet de faire coexister
`InMemory*Store` (défaut dev/tests) et `SQLAlchemy*Store` (production)
sans aucune branche `if` dans le code métier.

```mermaid
flowchart LR
    subgraph Ports["Ports (Protocol, inchangés)"]
        P1[DocumentStorePort]
        P2[CaseStorePort]
        P3[ResearchHistoryPort]
        P4["SessionStorePort (nouveau, additif)"]
        P5["DocumentStorePort (brouillons)"]
        P6[WorkspaceStorePort]
        P7[KnowledgeStorePort]
    end

    subgraph InMemory["Implémentations en mémoire (défaut dev/tests, conservées)"]
        M1[InMemoryDocumentStore]
        M2[InMemoryCaseStore]
        M3[InMemoryResearchHistory]
        M4[InMemorySessionStore]
        M5[InMemoryDocumentStore - drafts]
        M6[InMemoryWorkspaceStore]
        M7[InMemoryKnowledgeStore]
    end

    subgraph SQLAlchemy["Implémentations SQLAlchemy (nouvelles, Sprint 26)"]
        S1[SQLAlchemyDocumentStore]
        S2[SQLAlchemyCaseStore]
        S3[SQLAlchemyResearchHistory]
        S4[SQLAlchemySessionStore]
        S5[SQLAlchemyDraftDocumentStore]
        S6[SQLAlchemyWorkspaceStore]
        S7[SQLAlchemyKnowledgeStore]
    end

    P1 -.implémenté par.-> M1
    P1 -.implémenté par.-> S1
    P2 -.-> M2
    P2 -.-> S2
    P3 -.-> M3
    P3 -.-> S3
    P4 -.-> M4
    P4 -.-> S4
    P5 -.-> M5
    P5 -.-> S5
    P6 -.-> M6
    P6 -.-> S6
    P7 -.-> M7
    P7 -.-> S7

    S1 & S2 & S3 & S4 & S5 & S6 & S7 --> Base["tmis.core.db.base.Base\n(une seule Base déclarative,\nréexporte tmis.core.database.Base)"]
    Base --> Engine["Moteur sync (psycopg)\ntmis.core.database.engine\n(préexistant, socle identité/firm)"]
```

**Pourquoi les 7 stores SQLAlchemy sont tous synchrones** : les 7 ports
déclarent des méthodes `def`, jamais `async def` — un `Protocol` ne peut
pas changer de signature, donc un adaptateur qui l'implémente ne peut pas
devenir asynchrone non plus. Les 7 stores utilisent donc le moteur sync
déjà présent dans le dépôt (`tmis.core.database`), pas un second moteur.

## Le moteur asyncpg : seulement là où aucun port n'existe

`tmis.core.db.session` ajoute un second moteur, `asyncpg`, à côté du
moteur sync — mais il ne sert **pas** aux 7 stores ci-dessus. Il sert au
seul endroit du Sprint 26 qui lit des données en dehors de tout port :
l'historique complet des versions d'un document
(`GET /documents/{id}/versions`), puisque `DocumentStorePort` n'expose
que la dernière version par construction (`get(document_id)`).

```mermaid
flowchart TD
    Client([Client]) -->|"POST /api/v1/documents/upload\n(multipart)"| API[FastAPI]
    API -->|"1. save() version 1\nstatus=received"| SyncStore[SQLAlchemyDocumentStore\nmoteur sync]
    API -->|"2. .delay(document_id, filename,\ncontent_type, case_id)"| Celery[("Celery\n(broker/backend = redis_url)")]
    API -->|"202 Accepted\n{document_id, task_id}"| Client

    Celery -->|worker| DocTask["process_document_task\n(asyncio.run)"]
    DocTask -->|"pipeline.process(...)"| Pipeline[DocumentIntelligencePipeline\nSprint 3]
    Pipeline -->|"save() version 2\nstatus=processed\n(nouvelle ligne, jamais d'écrasement)"| SyncStore

    DocTask -->|"si case_id fourni\n.delay(case_id, document_id)"| CaseTask["trigger_case_workflow_task\n(asyncio.run)"]
    CaseTask -->|"ingest_document(...)"| Workflow[CaseIntelligenceWorkflow\nSprint 4]
    Workflow -->|"save()"| CaseStore[SQLAlchemyCaseStore\nmoteur sync]

    ClientV([Client]) -->|"GET /documents/{id}/versions"| VersionsEndpoint["endpoint version-history"]
    VersionsEndpoint -->|"select() ordonné par version"| AsyncEngine["AsyncSessionLocal\nmoteur asyncpg"]
    AsyncEngine -.->|"même table, même Base"| SyncStore
```

## Limite connue : deux vues de `CaseProfile` qui ne convergent pas encore

`case_intelligence.bootstrap.get_case_intelligence_workflow()` (Sprint 4,
utilisé par les endpoints synchrones `/api/v1/cases/*`) continue de
construire son `CaseIntelligenceWorkflow` avec `InMemoryCaseStore` par
défaut — ce câblage n'a pas été touché ce sprint, qui ajoute des
adaptateurs derrière les ports existants sans changer leur câblage par
défaut ailleurs dans le dépôt. Seul le nouveau chemin asynchrone
(`trigger_case_workflow_task`) construit un `CaseIntelligenceWorkflow`
avec `SQLAlchemyCaseStore`. Résultat : un dossier créé via
`POST /api/v1/cases/{id}/profile` et un dossier enrichi via l'upload
asynchrone d'un document ne sont, pour l'instant, pas la même ligne tant
qu'un sprint futur ne réconcilie pas ce câblage. C'est documenté ici et
dans le rapport d'audit plutôt que corrigé silencieusement, pour ne pas
élargir le périmètre du sprint à un changement de câblage partagé par de
nombreux tests existants (Sprint 4).

## Versionning des documents

`document_records` a une clé primaire de substitution (`id`, UUID) — pas
`document_id`. `save()` insère toujours une nouvelle ligne, jamais une
mise à jour en place ; `version` s'incrémente, `previous_version_id`
pointe vers la ligne précédente. `get(document_id)` (le seul accès que le
port expose) renvoie la version la plus récente ; `list_versions()`
(méthode supplémentaire, hors port, utilisée par l'endpoint d'historique)
renvoie tout l'historique, du plus ancien au plus récent.

## Migrations

Voir `docs/152-guide-migrations.md`. Une migration par domaine, chaînée
linéairement (`0001_document_record` → ... → `0007_knowledge_object`),
jamais une migration fourre-tout.
