import uuid
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.api.deps import get_current_firm_id
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.core.database import get_db_session
from tmis.legal_drafting.documents.adapters import (
    CaseIntelligenceCaseAdapter,
    LegalReasoningAdapter,
    LegalResearchAdapter,
)
from tmis.legal_drafting.documents.orchestrator import DocumentOrchestrator
from tmis.legal_drafting.documents.sqlalchemy_store import SQLAlchemyDraftDocumentStore
from tmis.legal_drafting.history.store import InMemoryDraftHistory
from tmis.legal_drafting.style.engine import StyleEngine
from tmis.legal_drafting.style.registry import StyleProfileRegistry
from tmis.legal_drafting.templates.registry import TemplateRegistry
from tmis.legal_drafting.validation.service import HumanInTheLoopService
from tmis.legal_drafting.versioning.sqlalchemy_service import SQLAlchemyVersioningService
from tmis.legal_reasoning.bootstrap import get_reasoning_orchestrator
from tmis.legal_research.bootstrap import get_research_orchestrator

# ----------------------------------------------------------------------
# Stateless collaborators — process-wide singletons (ADR-SLICE-02, see
# docs/28-legal-drafting.md). None of these hold anything that varies by
# tenant or by draft: the template outlines and style profiles are fixed
# reference data, and the style engine is a pure formatter. Caching them
# is a performance choice, not an isolation risk.
# ----------------------------------------------------------------------


@lru_cache
def get_template_registry() -> TemplateRegistry:
    return TemplateRegistry()


@lru_cache
def get_style_registry() -> StyleProfileRegistry:
    return StyleProfileRegistry()


@lru_cache
def get_style_engine() -> StyleEngine:
    return StyleEngine()


# ----------------------------------------------------------------------
# History / validation — still process-wide singletons, still in-memory
# (documented debt, see docs/28-legal-drafting.md § dette technique and
# the sprint's own "Out of scope" section: their persistence and firm
# isolation are deliberately deferred, not silently dropped). Building
# them per-request instead of caching them here would make `/history` and
# `/validate` state disappear between requests — worse than today, not
# better — so they stay singletons until they get their own persistence
# pass.
# ----------------------------------------------------------------------


@lru_cache
def get_draft_history() -> InMemoryDraftHistory:
    return InMemoryDraftHistory()


@lru_cache
def get_validation_service() -> HumanInTheLoopService:
    return HumanInTheLoopService()


def get_document_orchestrator(
    session: Session = Depends(get_db_session),
    firm_id: uuid.UUID = Depends(get_current_firm_id),
) -> DocumentOrchestrator:
    """Assembled fresh on every request (ADR-SLICE-02) — no longer an
    `lru_cache` singleton. Only the draft store and the version history
    are built here, on the request's own `Session` and scoped to the
    caller's `firm_id`: that is the one thing that must never be shared
    across requests or tenants. Everything else composes the same
    process-wide collaborators as before (kernel, upstream engines,
    stateless registries) — see docs/28-legal-drafting.md for why the
    Legal Drafting Studio never re-implements case analysis, research or
    reasoning. `get_research_orchestrator` is itself firm-scoped since
    ADR-RESEARCH-02 (docs/21-legal-research.md) — this request's own
    `session`/`firm_id` are threaded through to it so a drafting-
    triggered search is isolated exactly like a direct
    `/legal-research/search` call.
    """
    kernel = get_kernel()
    case_workflow = get_case_intelligence_workflow()
    research_orchestrator = get_research_orchestrator(session=session, firm_id=firm_id)
    reasoning_orchestrator = get_reasoning_orchestrator()

    return DocumentOrchestrator(
        kernel=kernel,
        case_port=CaseIntelligenceCaseAdapter(case_workflow),
        research_port=LegalResearchAdapter(research_orchestrator),
        reasoning_port=LegalReasoningAdapter(reasoning_orchestrator),
        template_registry=get_template_registry(),
        style_registry=get_style_registry(),
        style_engine=get_style_engine(),
        history=get_draft_history(),
        validation_service=get_validation_service(),
        document_store=SQLAlchemyDraftDocumentStore(session, firm_id),
        versioning_service=SQLAlchemyVersioningService(session, firm_id),
    )
