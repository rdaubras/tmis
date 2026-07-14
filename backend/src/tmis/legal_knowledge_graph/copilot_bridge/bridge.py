from dataclasses import replace

from tmis.legal_copilot_framework.context_engine.schemas import CopilotContext


def attach_graph_context(
    context: CopilotContext, snapshot: dict[str, tuple[str, ...]]
) -> CopilotContext:
    """The only touch point between the Legal Knowledge Graph and the
    Legal Copilot Framework's `ContextEngine` (Sprint 24) — a pure
    function, never a modification of `ContextEngine.build()` itself.
    A copilot works with or without the graph; this call only adds to
    an already-built `CopilotContext`."""
    return replace(context, graph_context=snapshot)
