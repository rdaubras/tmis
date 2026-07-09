from typing import Protocol

from tmis.ai.schemas.provider import ModelResponse, ProviderCapabilities


class ProviderPort(Protocol):
    """Port implemented by every interchangeable model provider adapter.

    `tmis.ai.kernel.TMISKernel` is the only caller: agents and business
    modules never hold a reference to a `ProviderPort` directly.
    """

    provider_name: str
    capabilities: ProviderCapabilities

    async def complete(self, prompt: str, *, model: str | None = None) -> ModelResponse: ...
