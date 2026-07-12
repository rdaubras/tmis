from tmis.business_platform.plans.schemas import Plan, PlanName


class InMemoryPlanStore:
    def __init__(self) -> None:
        self._plans: dict[str, Plan] = {}

    def save(self, plan: Plan) -> None:
        self._plans[plan.id] = plan

    def get(self, plan_id: str) -> Plan | None:
        return self._plans.get(plan_id)

    def list_versions(self, name: PlanName) -> list[Plan]:
        return sorted((p for p in self._plans.values() if p.name is name), key=lambda p: p.version)

    def list_latest(self) -> list[Plan]:
        latest: dict[PlanName, Plan] = {}
        for plan in self._plans.values():
            if not plan.active:
                continue
            current = latest.get(plan.name)
            if current is None or plan.version > current.version:
                latest[plan.name] = plan
        return list(latest.values())
