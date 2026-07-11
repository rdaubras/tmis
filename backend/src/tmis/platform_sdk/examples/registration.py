"""Registers the sprint's five example plugins — their manifests (in
`DEVELOPMENT` status, exactly like any newly authored plugin) into the
plugin registry, and their implementations into the safe in-memory
implementation registry `tmis.platform_sdk.plugin_loader` reads from.
An ordinary Python import, never dynamic code loading."""

from tmis.platform_sdk.examples.agent_droit_social import PLUGIN_ID as AGENT_DROIT_SOCIAL_ID
from tmis.platform_sdk.examples.agent_droit_social import AgentDroitSocialPlugin
from tmis.platform_sdk.examples.agent_fiscal import PLUGIN_ID as AGENT_FISCAL_ID
from tmis.platform_sdk.examples.agent_fiscal import AgentFiscalPlugin
from tmis.platform_sdk.examples.connector_ged import PLUGIN_ID as CONNECTOR_GED_ID
from tmis.platform_sdk.examples.connector_ged import ConnectorGedPlugin
from tmis.platform_sdk.examples.document_template_consultation import (
    PLUGIN_ID as DOCUMENT_TEMPLATE_ID,
)
from tmis.platform_sdk.examples.document_template_consultation import (
    DocumentTemplateConsultationPlugin,
)
from tmis.platform_sdk.examples.workflow_validation import PLUGIN_ID as WORKFLOW_VALIDATION_ID
from tmis.platform_sdk.examples.workflow_validation import WorkflowValidationPlugin
from tmis.platform_sdk.plugin_loader.store import InMemoryPluginImplementationRegistry
from tmis.platform_sdk.plugin_registry.store import InMemoryPluginRegistry
from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PluginType

EXAMPLE_MANIFESTS: tuple[PluginManifest, ...] = (
    PluginManifest(
        id=AGENT_FISCAL_ID,
        name="Agent Fiscal",
        version="1.0.0",
        plugin_type=PluginType.AGENT,
        author="TMIS Labs",
        description="Agent d'analyse fiscale, exemple d'utilisation de agent_sdk.",
        license="MIT",
        permissions=frozenset({"access_knowledge", "access_research"}),
    ),
    PluginManifest(
        id=AGENT_DROIT_SOCIAL_ID,
        name="Agent Droit Social",
        version="1.0.0",
        plugin_type=PluginType.AGENT,
        author="TMIS Labs",
        description="Agent d'analyse en droit social, second exemple de agent_sdk.",
        license="MIT",
        permissions=frozenset({"access_knowledge", "access_research"}),
    ),
    PluginManifest(
        id=CONNECTOR_GED_ID,
        name="Connecteur GED",
        version="1.0.0",
        plugin_type=PluginType.CONNECTOR,
        author="TMIS Labs",
        description="Connecteur d'exemple vers une gestion électronique de documents.",
        license="MIT",
        permissions=frozenset({"read_documents"}),
    ),
    PluginManifest(
        id=WORKFLOW_VALIDATION_ID,
        name="Workflow Validation",
        version="1.0.0",
        plugin_type=PluginType.WORKFLOW,
        author="TMIS Labs",
        description="Workflow de validation de dépense à embranchement conditionnel.",
        license="MIT",
        permissions=frozenset(),
    ),
    PluginManifest(
        id=DOCUMENT_TEMPLATE_ID,
        name="Modèle de consultation",
        version="1.0.0",
        plugin_type=PluginType.DOCUMENT_TEMPLATE,
        author="TMIS Labs",
        description="Modèle documentaire de consultation, exemple de document_sdk.",
        license="MIT",
        permissions=frozenset({"create_drafts"}),
    ),
)


def register_example_plugins(
    registry: InMemoryPluginRegistry, implementations: InMemoryPluginImplementationRegistry
) -> None:
    for manifest in EXAMPLE_MANIFESTS:
        if registry.get(manifest.id) is None:
            registry.register(manifest)
    implementations.register(AGENT_FISCAL_ID, AgentFiscalPlugin)
    implementations.register(AGENT_DROIT_SOCIAL_ID, AgentDroitSocialPlugin)
    implementations.register(CONNECTOR_GED_ID, ConnectorGedPlugin)
    implementations.register(WORKFLOW_VALIDATION_ID, WorkflowValidationPlugin)
    implementations.register(DOCUMENT_TEMPLATE_ID, DocumentTemplateConsultationPlugin)
