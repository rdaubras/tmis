import pytest

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_drafting.bootstrap import get_document_orchestrator
from tmis.legal_drafting.export.schemas import ExportFormat
from tmis.legal_drafting.templates.schemas import DocumentType
from tmis.legal_drafting.validation.schemas import DraftDecision
from tmis.legal_reasoning.bootstrap import get_reasoning_orchestrator
from tmis.legal_research.bootstrap import get_research_orchestrator

# The Sprint 2 mock connectors do a naive substring match (see
# docs/21-legal-research.md), so any question routed to legal research
# must literally contain a substring of the `codes` fixture ("Le
# contrat de travail à durée indéterminée peut être rompu...").
_QUESTION = "contrat de travail à durée indéterminée peut être rompu"


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    """All bootstrap accessors are `lru_cache`d process-wide singletons;
    reset them before each test so state from one test never leaks into
    another (see docs/28-legal-drafting.md)."""
    get_document_orchestrator.cache_clear()
    get_reasoning_orchestrator.cache_clear()
    get_research_orchestrator.cache_clear()
    get_case_intelligence_workflow.cache_clear()
    get_kernel.cache_clear()


@pytest.mark.asyncio
async def test_create_draft_reaches_every_upstream_engine_end_to_end() -> None:
    workflow = get_case_intelligence_workflow()
    profile = workflow.case_store.get_or_create("case-1", title="Dossier test")
    profile.facts.append(
        Fact(
            id="fact-1",
            description="Le contrat de travail à durée indéterminée a été rompu le 3 mars.",
            confidence=0.8,
            source_document_ids={"doc-1"},
        )
    )
    workflow.case_store.save(profile)

    orchestrator = get_document_orchestrator()
    document = await orchestrator.create_draft(
        DocumentType.CONSULTATION,
        case_id="case-1",
        question=_QUESTION,
        variables={"client_name": "Dupont", "firm_name": "Cabinet Test"},
    )

    assert document.is_draft is True
    facts_section = next(s for s in document.sections if s.key == "facts")
    assert facts_section.paragraphs[0].fact_ids == ("fact-1",)

    legal_discussion = next(s for s in document.sections if s.key == "legal_discussion")
    assert legal_discussion.paragraphs[0].reference_ids
    assert any(c.source_type == "research_result" for c in document.citations)


@pytest.mark.asyncio
async def test_create_draft_without_case_or_question_still_produces_boilerplate_sections() -> None:
    orchestrator = get_document_orchestrator()
    document = await orchestrator.create_draft(DocumentType.NOTE_INTERNE)

    assert document.sections
    header = next(s for s in document.sections if s.key == "header")
    assert header.paragraphs


@pytest.mark.asyncio
async def test_full_lifecycle_regenerate_validate_export() -> None:
    orchestrator = get_document_orchestrator()
    document = await orchestrator.create_draft(
        DocumentType.COURRIER, question=_QUESTION, variables={"firm_name": "Cabinet Test"}
    )

    regenerated = await orchestrator.regenerate_section(document.id, "context")
    assert regenerated.id == document.id

    orchestrator.validate(document.id, DraftDecision.APPROVED, "avocat@cabinet.fr")
    validated_document = orchestrator.get_document(document.id)
    assert validated_document is not None
    assert validated_document.is_draft is True

    result = orchestrator.export(document.id, ExportFormat.HTML)
    assert result.content

    history = orchestrator.history(document.id)
    assert len(history) >= 3
