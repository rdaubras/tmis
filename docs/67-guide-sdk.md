# Guide du SDK TMIS (Sprint 13)

## Le contrat commun : `PluginPort`

```python
class PluginPort(Protocol):
    id: str
    plugin_type: PluginType
    async def invoke(self, context: PluginContext, payload: dict) -> dict: ...
```

C'est la **seule** chose que `tmis.platform_sdk.sandbox` et
`tmis.platform_sdk.plugin_loader` connaissent d'un plugin — peu
importe son type. Chaque SDK spécialisé (`agent_sdk`, `connector_sdk`,
`document_sdk`, `workflow_sdk`) fournit une classe de base qui
implémente `invoke()` pour vous, en l'adaptant vers une méthode métier
plus ergonomique que vous, en tant qu'auteur de plugin, redéfinissez.

## `PluginContext` : ce qu'un plugin reçoit

```python
@dataclass(frozen=True, slots=True)
class PluginContext:
    firm_id: str
    actor_id: str
    plugin_id: str
    events: EventPublisherPort       # publier un évènement (tmis.platform_sdk.events_sdk)
    permissions: PermissionCheckerPort  # vérifier une permission accordée
    kernel: KernelPort | None = None    # accès au TMIS AI Kernel (agents uniquement)
    config: dict[str, Any] = field(default_factory=dict)
```

Un plugin **n'importe jamais** un module métier interne directement —
tout ce dont il a besoin lui est injecté via ces trois ports. C'est ce
qui permet au sandbox d'auditer et de contrôler chaque appel : le
plugin n'a tout simplement pas d'autre chemin vers le reste de TMIS.

## Les cinq SDK spécialisés

| SDK | Classe de base | Méthode à implémenter | Guide |
|---|---|---|---|
| Agent | `agent_sdk.BaseAgentPlugin` | `run(context, agent_input) -> AgentOutput` | docs/66 (tutoriel) |
| Connecteur | `connector_sdk.BaseConnectorPlugin` | `fetch_page(query, page) -> ConnectorPage` | docs/71-guide-connecteurs.md |
| Workflow | `workflow_sdk.BaseWorkflowPlugin` | aucune — 100 % déclaratif | docs/70-guide-workflows.md |
| Modèle documentaire | `document_sdk.BaseDocumentTemplatePlugin` | `render_section(key, variables) -> str` | — |
| Outil générique | `sdk.ports.PluginPort` directement | `invoke(context, payload) -> dict` | — |

## Pourquoi un agent ne peut pas appeler un fournisseur IA directement

`BaseAgentPlugin` ne donne accès au Kernel qu'au travers de
`context.kernel`, typé `tmis.ai_team.agents.ports.KernelPort` (le même
port étroit que les agents de `tmis.ai_team`, Sprint 11) :

```python
class KernelPort(Protocol):
    async def complete(self, prompt: str) -> str: ...
```

Aucune autre méthode n'est exposée — un agent ne peut ni changer de
fournisseur, ni contourner les garde-fous du Kernel (Sprint 2).

## Versionnement et compatibilité

`PluginManifest.compatibility` déclare la plage de versions du SDK
avec laquelle le plugin est compatible. Ce sprint compare une valeur
exacte (`SDK_VERSION = "1.0.0"`) ou le joker `"*"` — un vrai parseur de
plages sémantiques (`>=1.0,<2.0`) est un axe pour un sprint futur, une
fois plusieurs versions majeures du SDK réellement en circulation.
