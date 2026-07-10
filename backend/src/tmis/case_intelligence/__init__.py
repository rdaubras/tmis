"""Case Intelligence Engine (CIE): TMIS's main business engine.

Where the Document Intelligence Engine (`tmis.document_intelligence`,
Sprint 3) understands a single document, the CIE reasons at the level of
a whole case: it aggregates everything the DIE produces (entities,
timeline events, chunks) across every document of a dossier into a
living, continuously-enriched `CaseProfile`.

No module here calls a model provider directly — any AI-assisted
capability (e.g. the executive summary) goes through
`tmis.ai.kernel.TMISKernel`. See docs/19-case-intelligence.md.
"""
