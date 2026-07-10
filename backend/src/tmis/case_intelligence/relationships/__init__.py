"""Relationship Engine: a graph connecting actors, documents, events,
facts and exhibits — the foundation for a future Legal Knowledge Graph
(see docs/19-case-intelligence.md).

Independent of `tmis.document_intelligence.knowledge` (the per-document
knowledge graph, Sprint 3) and of `tmis.ai.rag` (the vector store): this
graph answers "what is connected to what" at case scope, never "what is
semantically similar".
"""
