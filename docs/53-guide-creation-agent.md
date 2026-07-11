# Guide de création d'un agent (Sprint 11)

## Ce qu'est un agent dans TMIS

Un agent AI Team a une identité déclarative (`AgentDescriptor`, dans le
registre) **et** un comportement d'exécution (`TeamAgentPort`). Les
deux sont volontairement séparés : le registre peut lister un agent
sans que son implémentation existe encore (marketplace), et une
implémentation ne s'expose au reste du système qu'une fois enregistrée.

## 1. Décrire l'agent (`AgentDescriptor`)

```python
from tmis.ai_team.registry.schemas import AgentDescriptor
from tmis.ai_team.agents.schemas import AgentRole

descriptor = AgentDescriptor(
    id="agent-mon-expert",
    name="Mon Expert",
    role=AgentRole.GDPR_EXPERT,   # ou un nouveau rôle si nécessaire
    description="...",
    skills=frozenset({"ma_competence"}),
    estimated_cost_usd=0.02,
    average_duration_seconds=6.0,
    quality_score=0.85,
)
```

`skills` alimente `AgentRegistryPort.list_by_skill` — c'est ce qui
permet au Team Builder et au Delegation Engine de trouver un agent par
compétence plutôt que par identifiant en dur.

## 2. Implémenter le comportement (`TeamAgentPort`)

**Aucun agent ne peut appeler un fournisseur LLM directement** — la
seule dépendance autorisée est `KernelPort`
(`tmis.ai_team.agents.ports.KernelPort`), une interface étroite d'un
seul appel :

```python
class KernelPort(Protocol):
    async def complete(self, prompt: str) -> str: ...
```

Pour la plupart des rôles, `PromptedTeamAgent` suffit — il transforme
un prompt système + le contexte reçu en un seul appel
`KernelPort.complete()` :

```python
from tmis.ai_team.agents.prompted_agent import PromptedTeamAgent

agent = PromptedTeamAgent(
    name="Mon Expert",
    role=AgentRole.GDPR_EXPERT,
    system_prompt="Tu es un expert RGPD. ...",
    kernel=kernel_port,
)
```

Un agent au comportement réellement différent (par exemple, un agent
qui appelle `TMISKernel.search_connectors()` avant de rédiger sa
réponse) implémente `TeamAgentPort` directement plutôt que d'étendre
`PromptedTeamAgent` :

```python
class MonAgentSurMesure:
    name = "Mon Agent"
    role = AgentRole.LEGAL_RESEARCHER

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        ...
```

## 3. Enregistrer l'agent

```python
from tmis.ai_team.registry.bootstrap import get_agent_registry

get_agent_registry().register(descriptor)
```

`register()` est appelable à tout moment — au bootstrap comme à
l'exécution (c'est le mécanisme que le marketplace utilisera plus tard
pour activer un agent tiers).

## Mémoire d'agent

Chaque agent dispose d'une mémoire courte (bornée, par mission) et
longue (non bornée, taguée) via `AgentMemoryPort` :

```python
memory_store.remember_short_term(agent_id, mission_id, "note de contexte")
memory_store.remember_long_term(agent_id, "expérience à retenir", tags=frozenset({"commercial"}))
```

L'implémentation en mémoire (`InMemoryAgentMemoryStore`) est
process-locale et non persistante — le port est le point d'extension
vers un stockage réel.

## Contraintes à respecter

1. **Jamais d'appel direct à un fournisseur ou un connecteur** — passer
   systématiquement par `KernelPort`.
2. **Toute décision doit rester explicable** — `AgentOutput.warnings`
   n'est jamais vide silencieusement quand une incertitude existe.
3. **Toute production reste un brouillon** — ne jamais présenter une
   sortie d'agent comme validée juridiquement.
