from fastapi import HTTPException

from tmis.identity_platform.abac.schemas import AbacAttributes
from tmis.identity_platform.bootstrap import get_authorization_engine, get_identity_context_engine
from tmis.identity_platform.permissions.schemas import Permission


def authorize_or_403(
    firm_id: str,
    user_id: str,
    permission: Permission,
    attributes: AbacAttributes | None = None,
) -> None:
    """The single call-site every other bounded context uses to pass
    through the EITP's central authorization engine before performing
    a sensitive action — "aucun module ne peut être utilisé sans
    passer par cette plateforme, toutes les autorisations passent par
    le moteur central" (sprint constraint). Deliberately thin: HTTP
    framework glue only, so `identity_platform.authorization.
    AuthorizationEngine` itself stays free of any FastAPI dependency.
    Every other bounded context (`workflow_automation`, `ai_governance`,
    `integration_hub`, `cabinet_knowledge`, `ai_team`, ...) imports this
    rather than reaching into `identity_platform` internals directly —
    see docs/104-guide-migration-identity-platform.md."""
    authorization = get_authorization_engine()
    identity_context = get_identity_context_engine()
    identity = identity_context.get_or_default(firm_id, user_id)
    decision = authorization.check(identity, permission, attributes)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason or "accès refusé")
