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
