"""The living case: `CaseIntelligenceWorkflow` reacts to every processed
document (via the Sprint 2 `EventBus`, shared with the Document
Intelligence Engine) and automatically re-enriches the case's actors,
facts, timeline, evidence, issues, knowledge graph and search index,
publishing the corresponding events (see docs/19-case-intelligence.md).
"""
