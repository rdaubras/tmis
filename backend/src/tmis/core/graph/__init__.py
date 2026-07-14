"""Generic in-memory graph storage shared by every bounded-context graph.

Deliberately independent from any specific graph's domain vocabulary
(`CaseNode`/`CaseEdge`, `KnowledgeNode`/`KnowledgeEdge`, ...): this
package only factors out the *mechanism* (dict of nodes, list of edges,
adjacency list) that `case_intelligence.relationships.InMemoryCaseGraph`
and `document_intelligence.knowledge.InMemoryKnowledgeGraph` were each
reimplementing identically. It knows nothing about case scope, document
scope, or cabinet scope, and exposes no port of its own — each existing
`*GraphPort` implementation composes it by delegation and keeps its own
domain-typed signature unchanged.
"""
