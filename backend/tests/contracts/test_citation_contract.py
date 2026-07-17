"""Contract test for `Citation` (`tmis.ai.schemas.citation`) and
`ResearchCitation` (`tmis.legal_research.citations.schemas`), and the
explicit adapter between them, `tmis.agents.citations.
research_citation_to_citation`.

The Sprint 43 audit flagged a latent risk in that adapter's callers
(`ResearchAgent`, `JurisprudenceAgent`, `WatchAgent`): they zip
`response.results` (a `ResearchOrchestrator.search()` return value) with
`get_citations(search_id)`'s `ResearchCitation` tuple using
`zip(..., strict=True)`, which only guarantees equal *length*, not
correct *pairing* — no existing test drove this from a real
`ResearchOrchestrator` run through to the adapted `Citation` objects, only
hand-built fixtures on either side of the adapter in isolation. This test
does, via the real, process-wide `get_shared_research_orchestrator()` singleton
(the same one `ResearchAgent`/`JurisprudenceAgent` use in production),
against the Sprint 2 fixture connectors (no PISTE credentials are
configured anywhere in this environment, see
docs/reports/sprint-43-rapport-audit.md).
"""

from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.agents.jurisprudence_agent import JurisprudenceAgent
from tmis.agents.research_agent import ResearchAgent
from tmis.ai.schemas.citation import Citation
from tmis.legal_research.bootstrap import get_shared_research_orchestrator
from tmis.legal_research.citations.schemas import ResearchCitation

# The Sprint 2 mock connectors do a naive substring match (see
# docs/21-legal-research.md), so the query must literally contain a
# substring of the `codes` fixture.
_QUERY = "contrat de travail à durée indéterminée peut être rompu"


def _agent_input() -> AgentInput:
    import uuid

    return AgentInput(task_id=uuid.uuid4(), case_id=None, context={"query": _QUERY})


async def test_research_agent_citations_are_correctly_paired_from_a_real_orchestrator_run() -> (
    None
):
    orchestrator = get_shared_research_orchestrator()
    agent = ResearchAgent(orchestrator=orchestrator)

    output = await agent.run(_agent_input())

    assert output.confidence in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW)
    results = output.result["results"]
    assert isinstance(results, list) and results, "fixture connectors must return at least one hit"

    search_id = output.result["search_id"]
    research_citations = orchestrator.get_citations(str(search_id))
    assert research_citations is not None
    assert len(research_citations) == len(results), (
        "ResearchOrchestrator.search() results and get_citations() must stay in lockstep — "
        "this is exactly the zip(strict=True) pairing assumption ResearchAgent/"
        "JurisprudenceAgent/WatchAgent rely on"
    )

    for citation in output.citations:
        assert isinstance(citation, Citation)
        assert citation.source_id
        assert citation.connector
        assert citation.reference


async def test_jurisprudence_agent_reuses_the_same_adapter_without_raising() -> None:
    """`JurisprudenceAgent` reuses `research_citation_to_citation` exactly
    as `ResearchAgent` does (see `tmis.agents.citations`) — confirm the
    shared adapter is consumable from this second real production caller
    too, not just the one it was extracted from."""
    orchestrator = get_shared_research_orchestrator()
    agent = JurisprudenceAgent(orchestrator=orchestrator)

    output = await agent.run(_agent_input())

    for citation in output.citations:
        assert isinstance(citation, Citation)


def test_research_citation_shape_matches_what_the_adapter_expects() -> None:
    """`ResearchCitation` (the LRE's own schema) must keep the fields
    `research_citation_to_citation` reads (`source_id`, `excerpt`,
    `reference`) — a structural pin so a future field rename in
    `legal_research.citations.schemas` is caught here instead of failing
    silently deep inside agent output construction."""
    field_names = {f.name for f in ResearchCitation.__dataclass_fields__.values()}
    assert {"source_id", "excerpt", "reference"} <= field_names
