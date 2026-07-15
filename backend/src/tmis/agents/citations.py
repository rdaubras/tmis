from tmis.ai.schemas.citation import Citation
from tmis.legal_research.citations.schemas import ResearchCitation
from tmis.legal_research.search.schemas import ResearchResult


def research_citation_to_citation(result: ResearchResult, citation: ResearchCitation) -> Citation:
    """Explicit adapter from the LRE's `ResearchCitation` to the agents
    contract's `Citation` (see `tmis.ai.schemas.citation`). Extracted from
    `ResearchAgent` (Sprint 33) so `JurisprudenceAgent` (Sprint 34) can
    reuse the exact same conversion instead of a second, parallel one —
    both agents build `result`/`citation` pairs from the same
    `ResearchOrchestrator.search()` / `get_citations()` ordering (see
    `ResearchOrchestrator.search`), so the matching `ResearchResult.
    connector` is the correct source for `Citation.connector` in both
    cases — the same field `RetrievedChunk.to_citation()` already expects
    a caller to supply explicitly.
    """
    return Citation(
        source_id=citation.source_id,
        connector=result.connector,
        excerpt=citation.excerpt,
        reference=citation.reference,
    )
