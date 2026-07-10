from typing import Protocol

from tmis.legal_drafting.style.schemas import StyleProfile


class StyleProfileRegistryPort(Protocol):
    """Port implemented by every interchangeable style-profile catalog."""

    def get(self, profile_id: str) -> StyleProfile | None: ...

    def get_default(self) -> StyleProfile: ...

    def register(self, profile: StyleProfile) -> None: ...


class StyleEnginePort(Protocol):
    """Port implemented by every interchangeable style post-processor."""

    def apply(self, text: str, profile: StyleProfile) -> str: ...

    def prompt_instructions(self, profile: StyleProfile) -> str: ...

    def closing_formula(self, profile: StyleProfile) -> str: ...
