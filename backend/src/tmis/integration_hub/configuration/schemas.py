from dataclasses import dataclass, field


@dataclass(slots=True)
class ConnectorConfiguration:
    """Per-firm, per-connector configuration — "chaque intégration est
    configurable indépendamment par le cabinet" (sprint requirement)."""

    connector_id: str
    firm_id: str
    values: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
