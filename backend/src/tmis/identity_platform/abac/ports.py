from typing import Protocol

from tmis.identity_platform.abac.schemas import AbacAttributes
from tmis.identity_platform.identity_context.schemas import IdentityContext


class AbacRulePort(Protocol):
    """One pluggable attribute-based rule. `AbacEngine.evaluate` is
    closed over this contract — a new rule registers without touching
    the engine, same extensibility pattern as `rbac.RbacEngine`."""

    def evaluate(self, identity: IdentityContext, attributes: AbacAttributes) -> bool: ...
