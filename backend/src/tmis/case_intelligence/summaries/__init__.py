"""Case Summary: generates an executive summary, a chronological summary,
a documentary summary, the case status, and the points still to clarify
(see docs/19-case-intelligence.md).

The executive summary is the one part of the CIE that benefits from a
model's synthesis — it is produced by calling `TMISKernel.complete()`
(never a raw provider), per the Sprint 4 constraint that no business
logic talks to an LLM directly.
"""
