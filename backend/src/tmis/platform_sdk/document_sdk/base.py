from abc import ABC, abstractmethod
from typing import Any

from tmis.platform_sdk.document_sdk.schemas import DocumentTemplateDefinition
from tmis.platform_sdk.plugin_system.schemas import PluginType
from tmis.platform_sdk.sdk.schemas import PluginContext


class MissingVariablesError(ValueError):
    pass


class BaseDocumentTemplatePlugin(ABC):
    """The sprint's "DOCUMENT TEMPLATE SDK": définir des variables,
    utiliser des sections, appeler des composants du Drafting Engine,
    intégrer des validations. Subclass and implement
    `render_section()` — `invoke()` validates the required variables
    are present, then renders every declared section in order."""

    plugin_type = PluginType.DOCUMENT_TEMPLATE

    def __init__(self, plugin_id: str, definition: DocumentTemplateDefinition) -> None:
        self.id = plugin_id
        self.definition = definition

    def validate_variables(self, provided: dict[str, Any]) -> list[str]:
        return [
            v.name
            for v in self.definition.variables
            if v.required and v.name not in provided
        ]

    @abstractmethod
    def render_section(self, section_key: str, variables: dict[str, Any]) -> str: ...

    async def invoke(self, context: PluginContext, payload: dict[str, Any]) -> dict[str, Any]:
        variables = dict(payload.get("variables", {}))
        missing = self.validate_variables(variables)
        if missing:
            raise MissingVariablesError(f"missing variables: {', '.join(missing)}")
        sections = sorted(self.definition.sections, key=lambda s: s.order)
        rendered = {s.key: self.render_section(s.key, variables) for s in sections}
        await context.events.publish(
            "DraftGenerated",
            {"plugin_id": self.id, "document_type": self.definition.document_type.value},
        )
        return {"document_type": self.definition.document_type.value, "sections": rendered}
