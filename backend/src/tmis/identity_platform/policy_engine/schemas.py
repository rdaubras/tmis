import uuid
from dataclasses import dataclass
from enum import StrEnum

from tmis.identity_platform.permissions.schemas import Permission
from tmis.identity_platform.roles.schemas import Role


class PolicyEffect(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


def new_policy_id() -> str:
    return f"idpol-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class Policy:
    """A configurable, firm-specific authorization policy — the
    sprint's own examples: "seuls les associés peuvent valider une
    consultation", "certains modèles IA sont réservés aux associés",
    "l'export est interdit pour certains rôles", "un brouillon
    stratégique nécessite une double validation", "certains workflows
    ne sont disponibles que pour une équipe donnée". Distinct from
    `ai_fabric.governance.GovernanceEngine` (model selection),
    `ai_governance.policy_engine.PolicyEngine` (AI production
    compliance) and `cabinet_knowledge.governance.GovernanceEngine`
    (knowledge validation status) — this one governs identity/access
    authorization decisions only, on the same
    same-role-different-scope principle already documented for those
    three."""

    id: str
    firm_id: str
    permission: Permission
    effect: PolicyEffect = PolicyEffect.DENY
    allowed_roles: frozenset[Role] = frozenset()
    denied_roles: frozenset[Role] = frozenset()
    restricted_to_team_id: str | None = None
    requires_second_validation: bool = False
    reason: str = ""
    active: bool = True


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str = ""
    requires_second_validation: bool = False
