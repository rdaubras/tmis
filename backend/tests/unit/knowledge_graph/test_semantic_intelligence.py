import pytest

from tmis.knowledge_graph.semantic_intelligence.engine import SemanticLinkEngine
from tmis.knowledge_graph.semantic_intelligence.store import InMemorySemanticLinkStore


@pytest.mark.asyncio
async def test_similar_texts_produce_a_semantic_link() -> None:
    engine = SemanticLinkEngine(InMemorySemanticLinkStore(), similarity_threshold=0.3)
    objects = [
        ("obj-1", "contrat de bail commercial résiliation"),
        ("obj-2", "contrat de bail commercial résiliation anticipée"),
        ("obj-3", "recette de cuisine italienne"),
    ]

    links = await engine.link_objects(objects)

    pairs = {(link.source_id, link.target_id) for link in links}
    assert ("obj-1", "obj-2") in pairs
    assert ("obj-1", "obj-3") not in pairs
    assert ("obj-2", "obj-3") not in pairs


@pytest.mark.asyncio
async def test_link_objects_with_fewer_than_two_objects_returns_empty() -> None:
    engine = SemanticLinkEngine(InMemorySemanticLinkStore())
    assert await engine.link_objects([("obj-1", "texte")]) == []
    assert await engine.link_objects([]) == []


@pytest.mark.asyncio
async def test_links_for_returns_persisted_links() -> None:
    engine = SemanticLinkEngine(InMemorySemanticLinkStore(), similarity_threshold=0.3)
    objects = [
        ("obj-1", "contrat de bail commercial"),
        ("obj-2", "contrat de bail commercial"),
    ]

    await engine.link_objects(objects)

    assert len(engine.links_for("obj-1")) == 1
    assert len(engine.links_for("obj-2")) == 1
    assert engine.links_for("unknown") == []


@pytest.mark.asyncio
async def test_dissimilar_texts_produce_no_link_at_default_threshold() -> None:
    engine = SemanticLinkEngine(InMemorySemanticLinkStore())
    objects = [
        ("obj-1", "contrat de bail commercial"),
        ("obj-2", "recette de cuisine italienne"),
    ]

    links = await engine.link_objects(objects)

    assert links == []
