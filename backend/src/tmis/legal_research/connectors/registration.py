from tmis.ai.connectors.manager import ConnectorManager
from tmis.legal_research.connectors.internal_documentation_connector import (
    InternalDocumentationConnector,
)
from tmis.legal_research.connectors.private_database_connector import (
    PrivateDatabaseConnector,
)


def register_legal_research_connectors(connector_manager: ConnectorManager) -> None:
    """Registers the LRE's own connectors on the Kernel's existing
    `ConnectorManager` (see docs/22-guide-nouveau-connecteur.md) rather
    than creating a parallel manager — the codes/jurisprudence/doctrine
    connectors from Sprint 2 and the LRE's connectors are interchangeable
    peers behind the same `ConnectorPort`."""
    connector_manager.register("internal_documentation", InternalDocumentationConnector())
    connector_manager.register("private_database", PrivateDatabaseConnector())
