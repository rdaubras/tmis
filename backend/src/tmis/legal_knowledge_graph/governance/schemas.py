import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_access_policy_id() -> str:
    return f"gap-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class NodeAccessPolicy:
    """Retention and confidentiality metadata for one graph node —
    "qui peut voir, qui peut modifier, qui peut publier, durée de
    conservation, niveau de confidentialité" (Sprint 25 Phase 8).
    `confidentiality_level` reuses `identity_platform.abac.
    AbacAttributes`'s own vocabulary rather than inventing a second
    one; the actual view/modify/publish decision is always taken by
    `identity_platform.authorization.AuthorizationEngine` (via
    `identity_platform.api.guard.authorize_or_403`), never by this
    class — it only carries the attributes that decision conditions
    on."""

    id: str
    firm_id: str
    node_id: str
    confidentiality_level: str = "standard"
    retention_days: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
