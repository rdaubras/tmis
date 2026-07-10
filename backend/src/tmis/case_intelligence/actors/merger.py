import uuid

from tmis.case_intelligence.actors.schemas import Actor, ActorType
from tmis.document_intelligence.schemas.entities import EntityType, ExtractedEntity

_ENTITY_TO_ACTOR_TYPE: dict[EntityType, ActorType] = {
    EntityType.PERSON: ActorType.PERSON,
    EntityType.COMPANY: ActorType.COMPANY,
    EntityType.JURISDICTION: ActorType.JURISDICTION,
}

_TITLE_PREFIXES = ("maître ", "me ", "m. ", "mme ", "mr ", "mrs ")


def normalize_name(name: str) -> str:
    """Strips common French civility titles so "Maître Jean Dupont" and
    "M. Jean Dupont" resolve to the same actor."""
    lowered = " ".join(name.strip().lower().split())
    for prefix in _TITLE_PREFIXES:
        if lowered.startswith(prefix):
            return lowered[len(prefix) :].strip()
    return lowered


class ActorMerger:
    """Implements `ActorMergerPort`: matches new entities against existing
    actors by normalized name or known alias, merging duplicates instead
    of creating a new actor for every document (see
    docs/19-case-intelligence.md).
    """

    def merge(
        self, actors: list[Actor], entities: list[ExtractedEntity], document_id: str
    ) -> list[Actor]:
        updated = list(actors)
        index: dict[tuple[ActorType, str], Actor] = {}
        for actor in updated:
            index[(actor.type, normalize_name(actor.name))] = actor
            for alias in actor.aliases:
                index[(actor.type, normalize_name(alias))] = actor

        for entity in entities:
            actor_type = _ENTITY_TO_ACTOR_TYPE.get(entity.type)
            if actor_type is None:
                continue
            key = (actor_type, normalize_name(entity.value))
            existing = index.get(key)
            if existing is not None:
                existing.aliases.add(entity.value)
                existing.source_document_ids.add(document_id)
                continue
            new_actor = Actor(
                id=str(uuid.uuid4()),
                type=actor_type,
                name=entity.value,
                aliases={entity.value},
                source_document_ids={document_id},
            )
            updated.append(new_actor)
            index[key] = new_actor

        return updated
