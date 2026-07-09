from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ConnectorDocument:
    """A document returned by any `ConnectorPort` implementation.

    Generic on purpose: the Connector Manager is meant to host connectors to
    legal sources today (codes, jurisprudence, doctrine) and to other
    document or internal sources in the future, without agents needing to
    know which kind of connector answered.
    """

    id: str
    title: str
    content: str
    connector: str
    metadata: dict[str, str] = field(default_factory=dict)
