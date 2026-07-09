"""RAG pipeline skeleton: ingestion -> cleaning -> chunking -> embeddings ->
indexing -> retrieval -> reranking -> citations.

No real external source is connected yet (see docs/09-roadmap-30-sprints.md,
Sprint 7-9); every stage has a working in-memory implementation so the full
pipeline is exercisable end-to-end today.
"""
