from tmis.cabinet_os.subscriptions.schemas import Subscription, UsageCounters


class InMemorySubscriptionStore:
    def __init__(self) -> None:
        self._subscriptions: dict[str, Subscription] = {}

    def get(self, firm_id: str) -> Subscription | None:
        return self._subscriptions.get(firm_id)

    def save(self, subscription: Subscription) -> None:
        self._subscriptions[subscription.firm_id] = subscription


class InMemoryUsageStore:
    def __init__(self) -> None:
        self._usage: dict[str, UsageCounters] = {}

    def get(self, firm_id: str) -> UsageCounters | None:
        return self._usage.get(firm_id)

    def save(self, usage: UsageCounters) -> None:
        self._usage[usage.firm_id] = usage
