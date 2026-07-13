from tmis.cloud_operations.alerting.schemas import AlertEvent, AlertRule


class InMemoryAlertRuleStore:
    def __init__(self) -> None:
        self._rules: dict[str, AlertRule] = {}

    def save(self, rule: AlertRule) -> None:
        self._rules[rule.id] = rule

    def get(self, rule_id: str) -> AlertRule | None:
        return self._rules.get(rule_id)

    def list_active(self, firm_id: str | None = None) -> list[AlertRule]:
        return [
            r
            for r in self._rules.values()
            if r.active and (firm_id is None or r.firm_id in (None, firm_id))
        ]


class InMemoryAlertEventStore:
    def __init__(self) -> None:
        self._events: list[AlertEvent] = []

    def save(self, event: AlertEvent) -> None:
        self._events.append(event)

    def list_for_firm(self, firm_id: str | None) -> list[AlertEvent]:
        return [e for e in self._events if e.firm_id == firm_id]

    def list_all(self) -> list[AlertEvent]:
        return list(self._events)
