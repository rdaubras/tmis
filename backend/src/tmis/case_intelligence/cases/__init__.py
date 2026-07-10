"""Case Model: `CaseProfile` is the living, continuously-enriched
aggregate at the heart of the Case Intelligence Engine (see
docs/19-case-intelligence.md).

`CaseProfile` is keyed by `case_id`, the same identifier as the
lightweight, persisted `tmis.domain.case.entities.Case` row (Sprint 1).
That row remains the source of truth for a case's existence, ownership
and billing-relevant status; `CaseProfile` is the in-memory enrichment
layer the CIE builds on top of it. Real persistence for `CaseProfile`
lands with the `document`/`case` bounded contexts (Sprint 6-7, see
docs/09-roadmap-30-sprints.md) — the exact pattern already used for
`tmis.document_intelligence.schemas.record.DocumentRecord` in Sprint 3.
"""
