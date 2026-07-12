from tmis.workflow_automation.rule_engine.schemas import Rule


class InMemoryRuleStore:
    def __init__(self) -> None:
        self._rules: dict[tuple[str, str], Rule] = {}

    def add(self, rule: Rule) -> None:
        self._rules[(rule.firm_id, rule.id)] = rule

    def get(self, firm_id: str, rule_id: str) -> Rule | None:
        return self._rules.get((firm_id, rule_id))

    def list_for_firm(self, firm_id: str) -> list[Rule]:
        return [r for (fid, _), r in self._rules.items() if fid == firm_id]
