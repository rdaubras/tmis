"""Cross-cutting domain ports shared across bounded contexts.

`ModelProviderPort` and `LegalSourceConnectorPort` are the interchangeability
seams described in docs/03-architecture-technique.md: no bounded context or
agent talks to a model SDK or an external legal database directly.
"""
