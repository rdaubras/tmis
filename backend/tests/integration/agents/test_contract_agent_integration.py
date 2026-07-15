"""End-to-end: a contract persisted through `DocumentStorePort` (Sprint 26) is
confronted to the firm's real clause library (`ClauseEngine`, Sprint 12, backed
by a real `KnowledgeSpace`) by the real `ContractAgent` (Sprint 35), producing
risk/missing-clause findings, a generative synthesis through the real
`TMISKernel.complete()`, and a governance explainability report."""

import uuid

import pytest

from tmis.agents.contract_agent import ContractAgent
from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.ai.kernel.kernel import TMISKernel
from tmis.ai_governance.bootstrap import get_ai_governance_platform
from tmis.cabinet_knowledge.clauses.engine import ClauseEngine
from tmis.cabinet_knowledge.clauses.schemas import ClauseVariant
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.record import DocumentRecord
from tmis.document_intelligence.storage.in_memory_store import InMemoryDocumentStore

_FIRM_ID = "firm-integration"


def _seed_clause_library() -> ClauseEngine:
    clause_engine = ClauseEngine(KnowledgeSpace(InMemoryKnowledgeStore()))
    clause_engine.create_clause(
        _FIRM_ID,
        "Clause de limitation de responsabilité",
        LegalDomain.COMMERCIAL,
        "limitation_responsabilite",
        (
            ClauseVariant(
                id="v-risk",
                text="La responsabilite du prestataire est totalement exclue en toute circonstance",
                notes="Variante a risque : exclusion totale defavorable au client",
            ),
        ),
        author="sprint35-integration-test",
    )
    clause_engine.create_clause(
        _FIRM_ID,
        "Clause de non-concurrence",
        LegalDomain.COMMERCIAL,
        "non_concurrence",
        (ClauseVariant(id="v-nc", text="Interdiction de concurrence pendant douze mois"),),
        author="sprint35-integration-test",
    )
    return clause_engine


@pytest.mark.asyncio
async def test_persisted_contract_flows_through_document_store_clause_engine_and_agent() -> None:
    document_store = InMemoryDocumentStore()
    document = DocumentRecord(
        document_id=str(uuid.uuid4()),
        filename="contrat-prestation-informatique.pdf",
        status=ProcessingStatus.STORED,
        raw_bytes=b"%PDF-1.4 fake",
        ocr_text=(
            "Contrat de prestation informatique entre la SSII et le Client.\n\n"
            "Clause de limitation de responsabilité : la responsabilite du "
            "prestataire est totalement exclue en toute circonstance.\n\n"
            "Article final : droit applicable francais."
        ),
    )
    document_store.save(document)

    clause_engine = _seed_clause_library()
    governance = get_ai_governance_platform()

    agent = ContractAgent(
        kernel=TMISKernel(),
        document_store=document_store,
        clause_engine=clause_engine,
        governance=governance,
        firm_id=_FIRM_ID,
    )

    task_id = uuid.uuid4()
    agent_input = AgentInput(
        task_id=task_id, case_id=None, context={"document_id": document.document_id}
    )

    output = await agent.run(agent_input)

    findings = {f["clause_type"]: f for f in output.result["clauses"]}
    assert findings["limitation_responsabilite"]["status"] == "present"
    assert "risque" in findings["limitation_responsabilite"]["risk_notes"].lower()
    assert findings["non_concurrence"]["status"] == "missing"

    assert output.result["synthesis"]
    assert output.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)
    assert output.citations[0].source_id == document.document_id

    report = governance.explainability.latest(_FIRM_ID, str(task_id))
    assert report is not None
    assert document.document_id in report.documents_consulted


@pytest.mark.asyncio
async def test_two_persisted_contract_versions_produce_a_paragraph_diff() -> None:
    document_store = InMemoryDocumentStore()
    version_1 = DocumentRecord(
        document_id=str(uuid.uuid4()),
        filename="contrat-v1.pdf",
        status=ProcessingStatus.STORED,
        raw_bytes=b"%PDF-1.4 fake",
        ocr_text="Article 1 : Duree de douze mois.\n\nArticle 2 : Prix forfaitaire de 10000 EUR.",
    )
    version_2 = DocumentRecord(
        document_id=str(uuid.uuid4()),
        filename="contrat-v2.pdf",
        status=ProcessingStatus.STORED,
        raw_bytes=b"%PDF-1.4 fake",
        ocr_text=(
            "Article 1 : Duree de vingt-quatre mois.\n\n"
            "Article 2 : Prix forfaitaire de 10000 EUR.\n\n"
            "Article 3 : Clause de confidentialite ajoutee."
        ),
    )
    document_store.save(version_1)
    document_store.save(version_2)

    agent = ContractAgent(
        kernel=TMISKernel(),
        document_store=document_store,
        clause_engine=_seed_clause_library(),
        firm_id=_FIRM_ID,
    )

    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=None,
        context={
            "document_id": version_1.document_id,
            "compare_document_id": version_2.document_id,
        },
    )

    output = await agent.run(agent_input)

    diff = output.result["version_diff"]
    assert diff is not None
    assert any("vingt-quatre" in entry["after"] for entry in diff["changed_paragraphs"])
    assert any("confidentialite" in p.lower() for p in diff["added_paragraphs"])
    assert diff["removed_paragraphs"] == []
    assert len(output.citations) == 2
