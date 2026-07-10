from dataclasses import dataclass
from enum import Enum


class SourceCategory(str, Enum):
    """The families of legal source a connector can belong to (see
    docs/21-legal-research.md — the LRE prepares for all of these even
    though Sprint 5 only ships mock connectors)."""

    LEGISLATION = "legislation"
    JURISPRUDENCE = "jurisprudence"
    DOCTRINE = "doctrine"
    INTERNAL_DOCUMENTATION = "internal_documentation"
    PRIVATE_DATABASE = "private_database"


@dataclass(frozen=True, slots=True)
class SourceDescriptor:
    """Metadata about one connector's source, used by the Ranking Engine
    to weigh authority and by the API to describe available sources."""

    connector_name: str
    category: SourceCategory
    display_name: str
    authority_score: float
    description: str = ""
