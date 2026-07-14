from tmis.ai.connectors.manager import ConnectorManager
from tmis.ai.connectors.ports import ConnectorPort
from tmis.legal_research.connectors.internal_documentation_connector import (
    InternalDocumentationConnector,
)
from tmis.legal_research.connectors.private_database_connector import (
    PrivateDatabaseConnector,
)


def register_legal_research_connectors(
    connector_manager: ConnectorManager,
    *,
    internal_documentation: ConnectorPort | None = None,
    private_database: ConnectorPort | None = None,
) -> None:
    """Registers the LRE's own connectors on the Kernel's existing
    `ConnectorManager` (see docs/22-guide-nouveau-connecteur.md) rather
    than creating a parallel manager — the codes/jurisprudence/doctrine
    connectors from Sprint 2 and the LRE's connectors are interchangeable
    peers behind the same `ConnectorPort`.

    `internal_documentation`/`private_database` are optional so every
    existing caller keeps getting the Sprint 5 in-memory fixtures
    unchanged; a bootstrap that wants the Sprint 27 real adapters (see
    `tmis.legal_research.connectors.factory`) passes them in here.
    """
    connector_manager.register(
        "internal_documentation", internal_documentation or InternalDocumentationConnector()
    )
    connector_manager.register("private_database", private_database or PrivateDatabaseConnector())
