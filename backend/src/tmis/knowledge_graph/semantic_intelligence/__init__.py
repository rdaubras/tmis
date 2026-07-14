"""Semantic similarity between knowledge objects — genuinely new:
distinct from the "connected to" edges of the three existing graphs,
the same principle already documented in
`tmis.document_intelligence.knowledge.ports.KnowledgeGraphPort` for why
a document's knowledge graph and its vector index answer different
questions. Computed via `tmis.ai.embeddings`/`tmis.ai.rag` — never a
second embedding provider or vector index.
"""
