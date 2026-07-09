"""Interchangeable adapters implementing `tmis.ai.providers.ports.ProviderPort`.

No other package in TMIS is allowed to import a vendor SDK (OpenAI,
Anthropic, Mistral, ...) directly. Every LLM call goes through
`tmis.ai.kernel.TMISKernel.complete`, which resolves a provider from the
`ProviderRegistry` defined here. See docs/13-guides-extension.md for how to
add a new provider.
"""
