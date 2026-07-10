"""Document Intelligence Engine (DIE): TMIS's documentary core.

A cabinet works primarily with documents. The DIE does not just extract
text — it reconstructs the logical and documentary structure of a case:
layout, classification, metadata, entities, timeline, chunks, embeddings
and a knowledge graph, all wired through the AI Kernel built in Sprint 2
(`tmis.ai`) and never coupled to a specific parsing/OCR/classification
vendor. See docs/14-document-intelligence.md.
"""
