from tmis.workflow_automation.integrations.ports import IntegrationPort


class UnknownIntegrationError(KeyError):
    pass


class IntegrationRegistry:
    """Holds every registered `IntegrationPort` by name. `action_engine`'s
    `ACTION_CALL_INTEGRATION` handler (registered in a future sprint)
    is expected to look up its target integration here rather than
    hardcoding a connector."""

    def __init__(self) -> None:
        self._integrations: dict[str, IntegrationPort] = {}

    def register(self, integration: IntegrationPort) -> None:
        self._integrations[integration.name] = integration

    def get(self, name: str) -> IntegrationPort:
        integration = self._integrations.get(name)
        if integration is None:
            raise UnknownIntegrationError(name)
        return integration

    def list_names(self) -> list[str]:
        return list(self._integrations)
