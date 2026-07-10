# TMIS Backend

FastAPI backend for TMIS (Themis Intelligence System). See `/docs` at the
repository root for the product vision and architecture.

## Development

```bash
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn tmis.main:app --reload
```

## Tests

```bash
pytest
```

## Structure

See `docs/04-domain-driven-design.md` for the full bounded-context layout:
`domain/` (entities, ports), `application/` (use cases), `infrastructure/`
(repositories, file storage), `api/` (FastAPI routers), `agents/`
(business agents, Sprint 1).

The **AI Kernel** (`ai/`) is the single entry point for every AI
capability — model providers, connectors, memory, cache, events, prompts,
guardrails, evaluation, RAG, and the first LangGraph workflow. No other
package talks to a model provider or a connector directly. See
`docs/10-ai-kernel.md`, `docs/11-langgraph-architecture.md`,
`docs/12-rag-architecture.md` and `docs/13-guides-extension.md`.

The **Document Intelligence Engine** (`document_intelligence/`) is TMIS's
documentary core: ingestion, OCR, layout analysis, classification,
metadata, entity extraction, timeline construction, structural chunking,
embeddings, and a knowledge graph, orchestrated by
`DocumentIntelligencePipeline`. See `docs/14-document-intelligence.md` and
`docs/15-18` for the extension guides (parser, OCR engine, classifier,
knowledge graph).

The **Case Intelligence Engine** (`case_intelligence/`) is TMIS's main
business engine: it turns every document processed by the DIE into a
living, continuously-enriched `CaseProfile` — actors (deduplicated),
facts (with corroboration/contradiction), a consolidated timeline,
evidence links, potential legal issues, a relationship graph, unified
search, and summaries. `CaseIntelligenceWorkflow` reacts automatically to
`DocumentProcessed` events on the Kernel's shared `EventBus`. See
`docs/19-case-intelligence.md` and `docs/20-guide-nouveau-moteur-analyse.md`.

The **Legal Research Engine** (`legal_research/`) is TMIS's documentary
search engine: given a query, it prepares it (normalization, language
detection, keyword extraction, legal-synonym expansion), selects the
right connectors, runs a hybrid lexical + vector search, normalizes and
deduplicates results, ranks them (relevance, authority, freshness), and
attaches a traceable citation to each one — through a three-layer cache
and with every search recorded in history. It never produces a legal
opinion, only structured, referenced elements for an agent to reason
over, and it never talks to a connector or a model provider directly:
everything goes through `TMISKernel`. See `docs/21-legal-research.md`
and `docs/22-24` for the connector/ranking/citation extension guides.

The **Legal Reasoning Engine** (`legal_reasoning/`) is TMIS's
decision-support brain: given a question, it reads the case (via the
CIE), searches the law (via the LRE), builds several co-existing
hypotheses, gathers arguments and counter-arguments with their
provenance, links evidence, detects conflicts, scores confidence with
an explanation, proposes analytical strategies without ever picking a
winner, and produces a transparent synthesis through
`ReasoningOrchestrator`. It never replaces the lawyer, never produces a
final legal document, and the only model call in the whole engine is
the final synthesis, through `TMISKernel`. See
`docs/25-legal-reasoning.md`, `docs/26-guide-nouveau-moteur-raisonnement.md`
and `docs/27-guide-scores-confiance.md`.
