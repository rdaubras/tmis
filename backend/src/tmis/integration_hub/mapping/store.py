from tmis.integration_hub.mapping.schemas import MappingProfile


class InMemoryMappingProfileStore:
    def __init__(self) -> None:
        self._profiles: dict[tuple[str, str, str], MappingProfile] = {}

    def save(self, profile: MappingProfile) -> None:
        self._profiles[(profile.firm_id, profile.connector_id, profile.entity_type)] = profile

    def get(self, firm_id: str, connector_id: str, entity_type: str) -> MappingProfile | None:
        return self._profiles.get((firm_id, connector_id, entity_type))
