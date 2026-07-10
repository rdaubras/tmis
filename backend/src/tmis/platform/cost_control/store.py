from tmis.platform.cost_control.schemas import AlertThreshold, CostEntry


class InMemoryCostEntryStore:
    def __init__(self) -> None:
        self._entries: list[CostEntry] = []

    def save(self, entry: CostEntry) -> None:
        self._entries.append(entry)

    def list_all(self) -> list[CostEntry]:
        return list(self._entries)

    def list_for_firm(self, firm_id: str) -> list[CostEntry]:
        return [e for e in self._entries if e.firm_id == firm_id]

    def list_for_user(self, user_id: str) -> list[CostEntry]:
        return [e for e in self._entries if e.user_id == user_id]

    def list_for_case(self, case_id: str) -> list[CostEntry]:
        return [e for e in self._entries if e.case_id == case_id]

    def list_for_workflow(self, workflow_id: str) -> list[CostEntry]:
        return [e for e in self._entries if e.workflow_id == workflow_id]


class InMemoryAlertThresholdStore:
    def __init__(self) -> None:
        self._thresholds: dict[tuple[str, str], AlertThreshold] = {}

    def save(self, threshold: AlertThreshold) -> None:
        self._thresholds[(threshold.scope, threshold.scope_id)] = threshold

    def list_all(self) -> list[AlertThreshold]:
        return list(self._thresholds.values())
