"""Legal Collaboration Engine (LCE) — turns TMIS into a collaborative
legal workspace: teams, tasks, comments, approvals, notifications,
activity, presence, audit, and sharing, all scoped to a `Workspace`
(see docs/33-legal-collaboration.md).

Deliberately independent of AI: nothing in this package imports
`tmis.ai` — no model provider, no connector, no `TMISKernel`. It
publishes its own `CollaborationEvent`s on its own
`CollaborationEventBus` (see `event_bus.py`); any AI-facing module that
wants to react to a collaboration action (a comment added, a task
completed, an approval decided) subscribes to that bus instead of the
Legal Collaboration Engine depending on AI in any way.
"""
