"""Cross-graph entity resolution — the genuinely new capability of
Sprint 25: deciding that a person or organization referenced under
different identifiers in the three existing graphs is the same
real-world entity. Nothing else in TMIS does this; `case_intelligence.
relationships`, `document_intelligence.knowledge`, and
`cabinet_knowledge.ontology` each only know about ids local to their
own scope.

Any resolution below the confidence threshold is routed through
`tmis.ai_governance.human_validation.HumanValidationEngine` — this
module never builds a second human-validation mechanism.
"""
