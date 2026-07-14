"""Knowledge Graph Federation & Semantic Intelligence (Sprint 25).

`tmis.knowledge_graph` is deliberately **not** a fourth graph engine.
Three graphs already exist and keep their exact scope, unchanged:

- `tmis.case_intelligence.relationships` (`CaseGraphPort`, dossier scope)
- `tmis.document_intelligence.knowledge` (`KnowledgeGraphPort`, document scope)
- `tmis.cabinet_knowledge.ontology` (`OntologyEngine`/`RelationStorePort`, cabinet scope)

No submodule of `tmis.knowledge_graph` stores a raw node or edge — every
read of "what is connected to what" is delegated to one of the three
ports/engines above. This package only adds capabilities that are
genuinely absent everywhere else:

- `federation` — a pure read layer answering cross-scope queries by
  composing the three existing graphs, with zero storage of its own.
- `entity_resolution` — deciding that different identifiers across the
  three graphs denote the same real-world entity (nothing else in TMIS
  does this).
- `semantic_intelligence` — similarity relations computed from
  `tmis.ai` embeddings, explicitly distinct from the "connected to"
  edges of the three graphs.
- `analytics` — extends `tmis.cloud_operations.metrics.MetricCategory`
  rather than building a parallel metrics store.
- `governance` — extends `tmis.ai_governance.policy_engine.
  GovernancePolicyType` and composes `tmis.cabinet_knowledge.governance`
  rather than building a parallel policy engine.
- `copilot_bridge` — extends `tmis.legal_copilot_framework.
  knowledge_packs` so a Knowledge Pack can reference resolved entities
  and federated relations, rather than opening a second integration
  path to the copilots.

See docs/145-architecture-knowledge-graph.md and
docs/reports/sprint-25-rapport-audit.md.
"""
