# Guides d'extension du Kernel

Ces trois guides couvrent les points d'extension les plus fréquents du AI
Kernel. Dans les trois cas, la règle est la même : **on ajoute une
implémentation derrière un port existant**, on ne modifie jamais les
appelants.

## 1. Ajouter un nouveau fournisseur de modèle (`ProviderPort`)

1. Créer `backend/src/tmis/ai/providers/<nom>_provider.py` :

   ```python
   from tmis.ai.schemas.provider import ModelResponse, ProviderCapabilities

   class MonProvider:
       provider_name = "mon_provider"
       capabilities = ProviderCapabilities(supports_completion=True)
       default_model = "mon-modele"

       async def complete(self, prompt: str, *, model: str | None = None) -> ModelResponse:
           ...  # appel SDK réel ici
   ```

2. L'enregistrer dans `tmis.ai.providers.registry.ProviderRegistry`
   (ajout dans `_providers` pour un fournisseur natif, ou
   `provider_registry.register("mon_provider", MonProvider())` pour un
   fournisseur ajouté dynamiquement par un cabinet).
3. Aucune autre modification n'est nécessaire : `TMISKernel.complete(...,
   provider="mon_provider")` fonctionne immédiatement, et bénéficie déjà
   du cache, des garde-fous et de l'évaluation.
4. Ajouter un test unitaire vérifiant que `complete()` retourne un
   `ModelResponse` cohérent (voir `backend/tests/unit/ai/test_providers.py`
   pour le patron à suivre).

## 2. Ajouter un nouvel agent (`AgentPort`)

1. Créer l'agent dans `backend/src/tmis/agents/<nom>_agent.py`,
   implémentant `AgentPort` (`tmis.ai.schemas.agent`) :

   ```python
   from tmis.ai.schemas.agent import AgentInput, AgentOutput

   class MonAgent:
       name = "mon_agent"

       async def run(self, agent_input: AgentInput) -> AgentOutput:
           ...
   ```

2. **Ne jamais** importer un provider ou un connecteur directement dans
   l'agent : passer par un `TMISKernel` injecté (`kernel.complete(...)`,
   `kernel.search_connectors(...)`) une fois que l'agent a une véritable
   logique métier à exécuter.
3. Enregistrer l'agent auprès du Kernel : `kernel.register_agent("mon_agent",
   MonAgent())`.
4. Si l'agent doit s'insérer dans une orchestration LangGraph, ajouter un
   nœud dans un graphe dédié (voir `tmis.ai.langgraph.graph` pour le
   patron), plutôt que de modifier le graphe de démonstration `kernel_demo`.
5. Ajouter les tests unitaires de l'agent, plus un test d'intégration s'il
   participe à un workflow (voir
   `backend/tests/integration/ai/test_langgraph_workflow.py`).

## 3. Ajouter un nouveau connecteur (`ConnectorPort`)

1. Créer `backend/src/tmis/ai/connectors/<nom>_connector.py` :

   ```python
   from tmis.ai.connectors.exceptions import ConnectorAuthenticationError
   from tmis.ai.schemas.connector import ConnectorDocument

   class MonConnector:
       connector_name = "mon_connecteur"

       def __init__(self, api_key: str | None = None) -> None:
           self._api_key = api_key

       async def search(self, query, filters=None) -> list[ConnectorDocument]:
           if not self._api_key:
               raise ConnectorAuthenticationError(self.connector_name, "missing API key")
           ...  # appel réel ici

       async def fetch(self, document_id: str) -> ConnectorDocument | None:
           ...
   ```

2. L'enregistrer dans `ConnectorManager` :
   `connector_manager.register("mon_connecteur", MonConnector(api_key=...))`.
3. Le manager gère automatiquement l'activation/désactivation
   (`enable`/`disable`) et isole les erreurs : si `MonConnector` lève une
   `ConnectorError`, `ConnectorManager.search()` ignore ce connecteur et
   continue avec les autres plutôt que d'échouer entièrement.
4. Aucune modification des agents n'est nécessaire : ils continuent
   d'appeler `kernel.search_connectors(query)`, qui interroge tous les
   connecteurs activés (`config.default_connectors` peut être étendu pour
   inclure le nouveau connecteur par défaut).
5. Ajouter les tests (recherche, authentification manquante, isolement de
   panne) en suivant le patron de
   `backend/tests/unit/ai/test_connectors.py`.

## Principe commun aux trois guides

Dans les trois cas, on ajoute un fichier qui implémente un port existant
et on l'enregistre dans le registre correspondant
(`ProviderRegistry`/`ConnectorManager`/`TMISKernel._agents`). On ne touche
jamais à `TMISKernel`, à `tmis.ai.langgraph`, ni aux autres agents — c'est
la garantie d'extensibilité que le Sprint 2 met en place.
