from tmis.identity_platform.abac.ports import AbacRulePort
from tmis.identity_platform.abac.schemas import AbacAttributes
from tmis.identity_platform.identity_context.schemas import IdentityContext


class AbacEngine:
    """Attribute-Based Access Control: every registered rule must pass
    (AND semantics) — "les politiques sont évaluées dynamiquement"
    (sprint requirement). No rules registered means ABAC imposes no
    additional restriction beyond RBAC."""

    def __init__(self, rules: list[AbacRulePort] | None = None) -> None:
        self._rules: list[AbacRulePort] = list(rules) if rules is not None else []

    def register(self, rule: AbacRulePort) -> None:
        self._rules.append(rule)

    def evaluate(self, identity: IdentityContext, attributes: AbacAttributes) -> bool:
        return all(rule.evaluate(identity, attributes) for rule in self._rules)
