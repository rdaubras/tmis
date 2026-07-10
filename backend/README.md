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

The **Legal Drafting Studio** (`legal_drafting/`) is TMIS's
assisted-drafting engine: it turns what the DIE, CIE, LRE and LRE²
already produced into a draft document — templates (nine document
types, versioned), sections independently regenerable, paragraphs
carrying full traceability (facts/references/evidence/hypotheses),
citations anchored to the document/section/paragraph, a configurable
style per firm, a review engine that only ever reports issues, a
human-in-the-loop validation trail, versioning (snapshot/compare/
restore), and DOCX/PDF/HTML export. It never drafts alone and never
produces anything but a draft: `Document.is_draft` always returns
`True`, and the only model call in the whole engine lives in the
Paragraph Engine, through `TMISKernel`. See `docs/28-legal-drafting.md`,
`docs/29-guide-nouveau-modele-documentaire.md`,
`docs/30-guide-moteur-style.md`, `docs/31-guide-versioning.md` and
`docs/32-guide-exports.md`.

The **Legal Collaboration Engine** (`collaboration/`) turns TMIS into a
shared legal workspace: workspaces, member lifecycle, six-role RBAC
with per-member grant/revoke overrides, tasks bound to a configurable
workflow, comments with threaded replies and `@user`/`@team`/`@firm`
mentions, single/multiple approvals, extensible notification channels,
a filterable activity feed plus a separate compliance-grade audit
trail, presence/optimistic-locking scaffolding, and internal/secure-link
sharing — all composed by `WorkspaceEngine`. **It depends on no AI
provider and works independently of the TMIS AI Kernel**: no module
under `collaboration/` imports `tmis.ai`, enforced by a static test
(`tests/unit/collaboration/test_collaboration_ai_independence.py`).
Every action is published on its own `CollaborationEventBus`, so a
future AI module can react to collaboration activity without the LCE
ever depending on it. See `docs/33-legal-collaboration.md`,
`docs/34-guide-roles.md`, `docs/35-guide-permissions.md`,
`docs/36-guide-workflows.md`, `docs/37-guide-notifications.md` and
`docs/38-guide-validations.md`.

The **Cabinet Operating System** (`cabinet_os/`) turns TMIS into a
complete business platform for law firms: CRM (physical/legal-person
clients, contacts with relations, a 360° profile), a business calendar
with day/week/month/agenda views, hearings that auto-create their own
calendar event and reminder, a deadline engine that computes nothing
until a procedure-specific rule is registered, time tracking (manual,
timer, quick entry), billing (quotes, invoices, credit notes, payments
behind an interface-only payment gateway), subscriptions (Solo/Cabinet/
Entreprise plans with quotas), a cabinet-level document registry,
cabinet/collaborator/admin dashboards and analytics, PDF/Excel/CSV/HTML
report generation, per-firm settings, a platform administration portal,
and a public API (API keys, OAuth2 client-credentials, scopes, rate
limiting). **Every module is multi-tenant from inception** (`firm_id`
on every aggregate, the same tenant key as `collaboration.workspace.
Workspace.firm_id`) and **never depends on an AI provider directly** —
the one AI-adjacent feature (usage analytics) goes through
`TMISKernel.evaluator` behind a narrow `AIUsagePort`. See
`docs/39-cabinet-os.md`, `docs/40-guide-crm.md`,
`docs/41-guide-calendrier.md`, `docs/42-guide-facturation.md`,
`docs/43-guide-rapports.md`, `docs/44-guide-api-publique.md` and
`docs/45-guide-administration.md`.
