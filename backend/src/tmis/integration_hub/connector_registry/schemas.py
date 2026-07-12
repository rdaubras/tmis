from dataclasses import dataclass, field
from enum import StrEnum

from tmis.integration_hub.connector_framework.schemas import ConnectorCapability, ConnectorType


class ConnectorStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"


@dataclass(slots=True)
class ConnectorDescriptor:
    """Everything the registry knows about one connector —
    "identifiant, nom, version, éditeur, type, capacités,
    permissions, statut, configuration" (sprint requirement)."""

    id: str
    name: str
    version: str
    publisher: str
    connector_type: ConnectorType
    capabilities: frozenset[ConnectorCapability]
    permissions: tuple[str, ...] = field(default_factory=tuple)
    status: ConnectorStatus = ConnectorStatus.ACTIVE
    config_schema: dict[str, str] = field(default_factory=dict)
