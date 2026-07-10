"""Legal Drafting Studio (LDS) — TMIS's assisted-drafting engine.

It never drafts alone: it turns what the Document Intelligence Engine,
Case Intelligence Engine, Legal Research Engine, and Legal Reasoning
Engine already produced into a draft document — every paragraph
traceable to the facts, evidence, research results and hypotheses that
justify it (see docs/28-legal-drafting.md). Every document produced is,
and remains, a draft: `Document.is_draft` is an invariant that is never
settable to `False`. TMIS never presents a document as legally
validated — that decision belongs to the avocat alone.
"""
