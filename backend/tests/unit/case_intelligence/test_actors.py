from tmis.case_intelligence.actors.merger import ActorMerger, normalize_name
from tmis.case_intelligence.actors.schemas import ActorType
from tmis.document_intelligence.schemas.entities import EntityType, ExtractedEntity


def test_normalize_name_strips_civility_titles() -> None:
    assert normalize_name("Maître Jean Dupont") == "jean dupont"
    assert normalize_name("M. Jean Dupont") == "jean dupont"
    assert normalize_name("Mme Dupont") == "dupont"


def test_merge_creates_new_actor_from_entity() -> None:
    merger = ActorMerger()
    actors = merger.merge(
        [], [ExtractedEntity(type=EntityType.PERSON, value="Jean Dupont", confidence=0.6)], "doc-1"
    )
    assert len(actors) == 1
    assert actors[0].type == ActorType.PERSON
    assert actors[0].source_document_ids == {"doc-1"}


def test_merge_deduplicates_across_documents_by_normalized_name() -> None:
    merger = ActorMerger()
    actors = merger.merge(
        [],
        [ExtractedEntity(type=EntityType.PERSON, value="Maître Jean Dupont", confidence=0.6)],
        "doc-1",
    )
    actors = merger.merge(
        actors,
        [ExtractedEntity(type=EntityType.PERSON, value="M. Jean Dupont", confidence=0.6)],
        "doc-2",
    )

    assert len(actors) == 1
    assert actors[0].aliases == {"Maître Jean Dupont", "M. Jean Dupont"}
    assert actors[0].source_document_ids == {"doc-1", "doc-2"}


def test_merge_does_not_confuse_different_actor_types() -> None:
    merger = ActorMerger()
    actors = merger.merge(
        [],
        [
            ExtractedEntity(type=EntityType.PERSON, value="ACME", confidence=0.6),
            ExtractedEntity(type=EntityType.COMPANY, value="ACME", confidence=0.6),
        ],
        "doc-1",
    )
    assert len(actors) == 2
    assert {a.type for a in actors} == {ActorType.PERSON, ActorType.COMPANY}


def test_merge_ignores_entity_types_with_no_actor_mapping() -> None:
    merger = ActorMerger()
    actors = merger.merge(
        [], [ExtractedEntity(type=EntityType.AMOUNT, value="1500 EUR", confidence=0.6)], "doc-1"
    )
    assert actors == []


def test_merge_matches_by_known_alias() -> None:
    merger = ActorMerger()
    actors = merger.merge(
        [],
        [ExtractedEntity(type=EntityType.PERSON, value="Me Dupont", confidence=0.6)],
        "doc-1",
    )
    actors = merger.merge(
        actors,
        [ExtractedEntity(type=EntityType.PERSON, value="Me Dupont", confidence=0.6)],
        "doc-2",
    )
    assert len(actors) == 1
    assert actors[0].source_document_ids == {"doc-1", "doc-2"}
