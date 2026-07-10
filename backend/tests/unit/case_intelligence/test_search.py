import pytest

from tmis.case_intelligence.actors.schemas import Actor, ActorType
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.facts.schemas import Fact
from tmis.case_intelligence.search.engine import CaseSearchEngine
from tmis.case_intelligence.search.schemas import SearchResultKind


def _profile() -> CaseProfile:
    profile = CaseProfile(case_id="case-1", title="Dupont c. ACME")
    profile.actors = [
        Actor(id="a1", type=ActorType.PERSON, name="Jean Dupont", source_document_ids={"doc-1"})
    ]
    profile.facts = [
        Fact(id="f1", description="Contrat de bail commercial", confidence=0.7),
        Fact(id="f2", description="Recette de cuisine italienne", confidence=0.7),
    ]
    profile.document_ids = {"doc-1"}
    return profile


@pytest.mark.asyncio
async def test_reindex_then_search_returns_matching_fact_first() -> None:
    engine = CaseSearchEngine()
    await engine.reindex(_profile())

    results = await engine.search("bail commercial", top_k=1)

    assert results[0].kind == SearchResultKind.FACT
    assert "bail" in results[0].label.lower()


@pytest.mark.asyncio
async def test_reindex_indexes_actors() -> None:
    engine = CaseSearchEngine()
    await engine.reindex(_profile())

    results = await engine.search("Jean Dupont")

    assert any(r.kind == SearchResultKind.ACTOR for r in results)


@pytest.mark.asyncio
async def test_reindex_rebuilds_from_scratch_without_duplicating_results() -> None:
    engine = CaseSearchEngine()
    profile = _profile()
    await engine.reindex(profile)
    await engine.reindex(profile)

    results = await engine.search("bail commercial", top_k=10)

    fact_hits = [r for r in results if r.id == "f1"]
    assert len(fact_hits) == 1


@pytest.mark.asyncio
async def test_search_on_empty_profile_returns_no_results() -> None:
    engine = CaseSearchEngine()
    await engine.reindex(CaseProfile(case_id="case-1", title="Empty"))
    assert await engine.search("anything") == []
