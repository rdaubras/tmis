"""The single integration path from Sprint 25's knowledge graph
capabilities into a Legal Copilot's Knowledge Pack — extends
`tmis.legal_copilot_framework.knowledge_packs` additively
(`KnowledgePack.resolved_entity_ids`/`federated_relation_refs`) rather
than opening a second route into the copilots. Like every other
Knowledge Pack field, these are ids resolved fresh on every call
(through `entity_resolution` and `federation`), never a copy.
"""
