"""Cross-scope read layer.

`FederationQueryEngine` holds no state of its own — it only calls
`CaseGraphPort`, `KnowledgeGraphPort`, and `OntologyEngine`, the three
existing graph ports/engines, and reshapes their answers into a single
cross-scope view. Deliberately independent from `entity_resolution`:
federation answers "what is connected to this known id, in this
scope", `entity_resolution` answers "which ids across scopes are the
same real-world thing" — composing the two (as `copilot_bridge` and
callers do) is what makes the "tout ce qui touche l'entité X" query
possible, but federation itself never decides entity identity.
"""
