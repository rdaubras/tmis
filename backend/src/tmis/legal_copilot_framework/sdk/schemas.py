from dataclasses import dataclass, field

from tmis.ai_team.capabilities.schemas import LegalDomain


@dataclass(frozen=True, slots=True)
class CopilotSpec:
    """The declarative shape the sprint's Copilot SDK asks for:
    identifiant, nom, domaine juridique, description, version,
    dépendances, agents utilisés, modèles IA compatibles, workflows,
    documents, connaissances, permissions, métriques. Anyone can build
    one of these and pass it to `CopilotBuilder.build` — no framework
    code changes needed to add a new copilot."""

    id: str
    name: str
    domain: LegalDomain
    description: str
    version: str
    author: str = "unknown"
    compatibility: str = "*"
    dependencies: tuple[str, ...] = ()
    agent_ids: tuple[str, ...] = ()
    compatible_models: frozenset[str] = field(default_factory=frozenset)
    workflow_pack_ids: tuple[str, ...] = ()
    document_pack_ids: tuple[str, ...] = ()
    knowledge_pack_ids: tuple[str, ...] = ()
    reasoning_pack_ids: tuple[str, ...] = ()
    prompt_pack_id: str | None = None
    validation_policy_ids: tuple[str, ...] = ()
    permissions: frozenset[str] = field(default_factory=frozenset)
    metrics_enabled: bool = True
