from tmis.legal_drafting.style.schemas import StyleProfile

_DEFAULT_PROFILE = StyleProfile(id="default", firm_name="Cabinet par défaut")


class StyleProfileRegistry:
    """Implements `StyleProfileRegistryPort`: every cabinet can register
    its own writing charter, so the same Paragraph Engine produces
    differently-toned drafts depending on which firm asked for them (see
    docs/30-guide-moteur-style.md)."""

    def __init__(self) -> None:
        self._profiles: dict[str, StyleProfile] = {_DEFAULT_PROFILE.id: _DEFAULT_PROFILE}

    def register(self, profile: StyleProfile) -> None:
        self._profiles[profile.id] = profile

    def get(self, profile_id: str) -> StyleProfile | None:
        return self._profiles.get(profile_id)

    def get_default(self) -> StyleProfile:
        return self._profiles[_DEFAULT_PROFILE.id]
