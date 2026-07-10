"""Cabinet Operating System (COS) — Sprint 9.

Turns TMIS into a complete business platform for law firms: CRM,
calendar, hearings, deadlines, time tracking, billing, subscriptions,
documents, dashboards, analytics, reports, settings, administration and
a public API.

Every aggregate is scoped by ``firm_id`` (multi-tenant from inception —
the same tenant key already used by
``tmis.collaboration.workspace.Workspace.firm_id`` in Sprint 8).

Business modules never depend on an AI provider or connector directly —
any AI-backed feature (e.g. usage analytics) goes through
``tmis.ai.kernel`` behind a narrow port, exactly like every other TMIS
engine since Sprint 2. See docs/39-cabinet-os.md.
"""
