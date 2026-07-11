# Guide — Ajouter un fournisseur d'IA

L'AI Intelligence Fabric ne connaît jamais un fournisseur directement
("aucun module métier ne connaît directement un fournisseur"). Ajouter
un fournisseur se fait entièrement dans `tmis.ai.providers` (Sprint 2)
— la Fabric le voit automatiquement via `provider_registry`.

## 1. Implémenter `ProviderPort`

```python
# backend/src/tmis/ai/providers/my_provider.py
from tmis.ai.providers.ports import ProviderPort
from tmis.ai.schemas.provider import ModelResponse, ProviderCapabilities


class MyProvider:
    provider_name = "my-provider"
    capabilities = ProviderCapabilities(supports_completion=True)

    async def complete(self, prompt: str, *, model: str | None = None) -> ModelResponse:
        ...  # appel HTTP réel vers le fournisseur
        return ModelResponse(text=..., provider=self.provider_name, model=model or "default")
```

## 2. L'enregistrer dans `ProviderRegistry`

```python
# backend/src/tmis/ai/providers/registry.py
self._providers["my-provider"] = MyProvider()
```

## 3. Aucune modification requise dans `ai_fabric`

`ai_fabric.provider_registry.FabricProviderRegistry` est un ré-export
direct de `ProviderRegistry` — le nouveau fournisseur apparaît
immédiatement dans `GET /api/v1/ai-fabric/providers`.

## 4. Enregistrer au moins un modèle pour ce fournisseur

Un fournisseur seul ne suffit pas à ce que le routeur le considère :
voir docs/75-guide-ajout-modele.md pour enregistrer un
`ModelDescriptor` référençant `provider="my-provider"`.
