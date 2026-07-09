# AI Kernel — architecture (Sprint 2)

## Pourquoi un Kernel

Avant le Sprint 2, chaque agent risquait de finir par appeler un fournisseur
de modèle ou une source documentaire directement — recréant, dossier après
dossier, le même couplage fort que l'architecture DDD du Sprint 1 s'efforce
d'éviter partout ailleurs.

Le **TMIS AI Kernel** (`backend/src/tmis/ai/`) est le socle qui empêche
cela structurellement : **aucun code en dehors de `tmis.ai` n'importe un
SDK de fournisseur de modèle ou un connecteur documentaire**. Tout passe
par `TMISKernel`.

Le Sprint 2 ne développe aucune fonctionnalité métier : chaque
implémentation est volontairement minimale (échos déterministes, fixtures
en mémoire) mais **réellement exécutable**, sans appel réseau externe.

## Vue d'ensemble des modules

```mermaid
flowchart TB
    subgraph Base["Couche de base"]
        SCHEMAS[schemas]
    end

    subgraph Independent["Modules indépendants (dépendent uniquement de schemas)"]
        EVENTS[events]
        CACHE[cache]
        MEMORY[memory]
        PROVIDERS[providers]
        CONNECTORS[connectors]
        PROMPTS[prompts]
        GUARDRAILS[guardrails]
        EVALUATION[evaluation]
        TOOLS[tools]
        EMBEDDINGS[embeddings]
    end

    subgraph Composed["Modules composés"]
        RETRIEVAL[retrieval] --> EMBEDDINGS
        RERANKING[reranking]
        RAG[rag] --> RETRIEVAL
        RAG --> RERANKING
        RAG --> EMBEDDINGS
        LANGGRAPH[langgraph] --> SCHEMAS
    end

    subgraph Root["Racine de composition"]
        KERNEL[kernel.TMISKernel]
    end

    SCHEMAS --> Independent
    SCHEMAS --> Composed
    Independent --> KERNEL
    Composed --> KERNEL
```

Chaque module (à l'exception de `schemas`, la base commune) peut évoluer
indépendamment : changer de fournisseur de cache (Redis ↔ mémoire), de
fournisseur de modèle, ou de moteur de reranking ne touche aucun autre
module.

## `TMISKernel` — responsabilités

```mermaid
classDiagram
    class TMISKernel {
        +config: KernelConfig
        +provider_registry: ProviderRegistry
        +connector_manager: ConnectorManager
        +cache: CachePort
        +event_bus: EventBus
        +prompt_registry: PromptRegistry
        +tool_registry: ToolRegistry
        +guardrails: GuardrailPipeline
        +evaluator: Evaluator
        +rag: RagPipeline
        +conversation_memory: ConversationMemory
        +case_memory: CaseMemory
        +workflow_memory: WorkflowMemory
        +user_memory: UserMemory
        +register_agent(name, agent)
        +get_agent(name) AgentPort
        +register_workflow(name, graph)
        +run_workflow(name, question) KernelWorkflowState
        +complete(prompt, provider) ModelResponse
        +embed(texts) list~vector~
        +search_connectors(query) list~ConnectorDocument~
        +validate_output(output) list~str~
        +get_prompt(id, variables) str
        +run_tool(name, kwargs) object
        +publish_event(event)
    }
```

`TMISKernel` est la **racine de composition** (composition root) : elle
construit une implémentation par défaut de chaque port si aucune n'est
injectée, ce qui permet de l'instancier sans configuration (`TMISKernel()`)
en développement/tests, et de tout remplacer en production (Redis pour le
cache et la mémoire, un vrai fournisseur de modèle, etc.) sans changer une
ligne d'agent.

## Séquence : `TMISKernel.complete()`

```mermaid
sequenceDiagram
    actor Agent
    participant K as TMISKernel
    participant G as GuardrailPipeline
    participant C as CachePort
    participant P as ProviderRegistry
    participant Pr as Provider
    participant E as Evaluator

    Agent->>K: complete(prompt, provider)
    K->>G: validate_input(prompt)
    G-->>K: ok (ou GuardrailViolation)
    K->>C: get(cache_key)
    alt cache hit
        C-->>K: ModelResponse (JSON)
        K-->>Agent: ModelResponse
    else cache miss
        K->>P: get(provider_name)
        P-->>K: Provider
        K->>Pr: complete(prompt)
        Pr-->>K: ModelResponse
        K->>C: set(cache_key, response)
        K->>E: record(EvaluationMetrics)
        K-->>Agent: ModelResponse
    end
```

Cette même discipline (garde-fous → cache → appel réel → évaluation) est
répétée dans `search_connectors()` pour la recherche documentaire.

## Event Bus

```mermaid
flowchart LR
    UQ[UserQuestionReceived] --> Bus((EventBus))
    WS[WorkflowStarted] --> Bus
    RC[ResearchCompleted] --> Bus
    DG[DraftGenerated] --> Bus
    VC[VerificationCompleted] --> Bus
    WF[WorkflowFinished] --> Bus
    Bus --> Sub1[Abonné: audit / logs]
    Bus --> Sub2[Abonné: notifications - futur]
```

Les composants du Kernel ne s'appellent jamais directement entre eux : ils
publient des événements typés (`tmis.ai.events.events`) sur un bus
in-memory (`tmis.ai.events.bus.EventBus`). Un nouvel abonné (audit,
notification) s'ajoute avec `event_bus.subscribe(EventType, handler)` sans
toucher aux publishers.

## Configuration

`KernelConfig` (`tmis.ai.kernel.config`) est chargée depuis les variables
d'environnement (préfixe `TMIS_AI_`), sur le même modèle que
`tmis.core.config.Settings` :

| Variable | Rôle | Défaut |
|---|---|---|
| `TMIS_AI_DEFAULT_PROVIDER` | Fournisseur de modèle utilisé par défaut | `openai` |
| `TMIS_AI_DEFAULT_CONNECTORS` | Connecteurs interrogés par défaut | `codes,jurisprudence,doctrine` |
| `TMIS_AI_CACHE_TTL_SECONDS` | Durée de vie du cache des appels IA | `300` |
| `TMIS_AI_USE_CACHE` | Active/désactive le cache globalement | `true` |

## Portée du Sprint 2

- Aucune fonctionnalité métier (analyse de contrat, conclusions,
  recherche juridique réelle) n'est développée ici.
- Aucun appel réseau externe réel n'est effectué : les providers renvoient
  un écho déterministe et taggé, les connecteurs interrogent une fixture
  en mémoire.
- Tout est néanmoins **réellement exécutable de bout en bout** — voir
  `docs/11-langgraph-architecture.md` pour le workflow de démonstration et
  `backend/tests/integration/ai/` pour les preuves automatisées.
