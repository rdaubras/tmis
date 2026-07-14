from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class CopilotContext:
    """Everything a copilot's agents receive before they run — the
    aggregation the sprint asks for (contexte utilisateur/cabinet/
    dossier, pièces, connaissances pertinentes, politiques de
    sécurité, préférences rédactionnelles). `case_context`/`pieces`
    are caller-supplied rather than fetched from `case_intelligence`
    directly: the caller (a copilot execution flow already holding
    the case) passes what it already has, keeping this engine free of
    an unverified new cross-context dependency — see the Sprint 24
    audit report."""

    firm_id: str
    user_id: str
    case_id: str | None
    user_context: dict[str, str]
    firm_context: dict[str, str]
    case_context: dict[str, str]
    pieces: tuple[str, ...]
    relevant_knowledge_ids: tuple[str, ...]
    security_policies: tuple[str, ...]
    writing_preferences: dict[str, str]
    built_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    # Added in Sprint 25 (Legal Knowledge Graph) — optional, defaulted
    # empty so every Sprint 24 caller keeps working unchanged. Filled
    # by `legal_knowledge_graph.copilot_bridge.attach_graph_context`,
    # never by `ContextEngine` itself, which stays free of a
    # dependency on a package that did not exist at Sprint 24.
    graph_context: dict[str, tuple[str, ...]] = field(default_factory=dict)
