from tmis.workflow_automation.condition_engine.engine import ConditionEngine
from tmis.workflow_automation.condition_engine.schemas import Condition
from tmis.workflow_automation.rule_engine.ports import RuleStorePort
from tmis.workflow_automation.rule_engine.schemas import Rule, new_rule_id


class RuleEngine:
    """Creates, lists, deactivates and evaluates configurable rules.
    Delegates the actual boolean evaluation to `ConditionEngine` —
    this class owns only the rule's identity and lifecycle."""

    def __init__(self, store: RuleStorePort, condition_engine: ConditionEngine) -> None:
        self._store = store
        self._condition_engine = condition_engine

    def create_rule(
        self, firm_id: str, name: str, condition: Condition, description: str = ""
    ) -> Rule:
        rule = Rule(
            id=new_rule_id(), firm_id=firm_id, name=name, condition=condition,
            description=description,
        )
        self._store.add(rule)
        return rule

    def get(self, firm_id: str, rule_id: str) -> Rule:
        rule = self._store.get(firm_id, rule_id)
        if rule is None:
            raise KeyError(rule_id)
        return rule

    def list_rules(self, firm_id: str, active_only: bool = False) -> list[Rule]:
        rules = self._store.list_for_firm(firm_id)
        return [r for r in rules if r.active] if active_only else rules

    def deactivate_rule(self, firm_id: str, rule_id: str) -> Rule:
        rule = self.get(firm_id, rule_id)
        rule.active = False
        return rule

    def evaluate(self, firm_id: str, rule_id: str, context: dict[str, str]) -> bool:
        rule = self.get(firm_id, rule_id)
        if not rule.active:
            return False
        return self._condition_engine.evaluate(rule.condition, context)

    def evaluate_all(self, firm_id: str, context: dict[str, str]) -> list[Rule]:
        return [
            r
            for r in self.list_rules(firm_id, active_only=True)
            if self._condition_engine.evaluate(r.condition, context)
        ]
