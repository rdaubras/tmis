from tmis.legal_copilot_framework.copilot.schemas import LegalCopilot
from tmis.legal_copilot_framework.copilots import (
    contentieux,
    contrats,
    droit_fiscal,
    droit_social,
    droit_societes,
)
from tmis.legal_copilot_framework.copilots.deps import DemoCopilotDeps


def seed_demo_copilots(deps: DemoCopilotDeps) -> list[LegalCopilot]:
    """Builds and registers the sprint's five MVP copilots — Phase 12
    of the Sprint 24 prompt. One call per domain module, each
    demonstrating the full pack hierarchy (agents, prompt/knowledge/
    reasoning/document/workflow packs, validation policy) with
    fictional data. Not business logic — see each module's docstring
    for scope."""

    return [
        contentieux.build(deps),
        droit_societes.build(deps),
        droit_fiscal.build(deps),
        droit_social.build(deps),
        contrats.build(deps),
    ]
