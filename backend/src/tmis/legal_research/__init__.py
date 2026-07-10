"""Legal Research Engine (LRE) — documentary/legal search for TMIS agents.

Given a query, the LRE selects the right connectors, executes searches,
normalizes and deduplicates results, ranks them, and attaches traceable
citations — always through `TMISKernel`, never a source directly (see
docs/21-legal-research.md). It never produces a legal opinion: it only
prepares structured, referenced elements for an agent to reason over.
"""
