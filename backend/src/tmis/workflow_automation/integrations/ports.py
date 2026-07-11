from typing import Protocol

from tmis.workflow_automation.integrations.schemas import IntegrationResult


class IntegrationPort(Protocol):
    """One pluggable external-system connector — messaging, calendar,
    GED, e-signature, videoconference, ERP/comptabilité. "Aucune
    intégration spécifique n'est imposée dans ce sprint" (sprint
    requirement): this module only defines the extension point;
    concrete integrations register themselves in a future sprint
    without any change here."""

    name: str

    def call(self, action_type: str, context: dict[str, str]) -> IntegrationResult: ...
