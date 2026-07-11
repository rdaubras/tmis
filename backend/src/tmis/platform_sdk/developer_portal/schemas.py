from dataclasses import dataclass
from enum import StrEnum


class ResourceType(StrEnum):
    TUTORIAL = "tutorial"
    GUIDE = "guide"
    API_REFERENCE = "api_reference"
    EXAMPLE = "example"
    BEST_PRACTICE = "best_practice"


@dataclass(frozen=True, slots=True)
class PortalResource:
    id: str
    title: str
    type: ResourceType
    path: str
    summary: str
