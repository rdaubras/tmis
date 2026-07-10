from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StyleProfile:
    """A firm's writing charter: tone, level of detail, length, and
    register — configurable per cabinet (see docs/30-guide-moteur-style.md).
    """

    id: str
    firm_name: str
    tone: str = "formal"
    detail_level: str = "standard"
    length: str = "standard"
    register: str = "soutenu"
