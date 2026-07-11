from typing import Protocol

from tmis.workflow_automation.rule_engine.schemas import Rule


class RuleStorePort(Protocol):
    def add(self, rule: Rule) -> None: ...

    def get(self, firm_id: str, rule_id: str) -> Rule | None: ...

    def list_for_firm(self, firm_id: str) -> list[Rule]: ...
