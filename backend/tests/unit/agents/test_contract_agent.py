import uuid

import pytest

from tmis.agents.contract_agent import ContractAgent
from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.ai_fabric.bootstrap import get_ai_intelligence_fabric
from tmis.ai_governance.bootstrap import get_ai_governance_platform
from tmis.cabinet_knowledge.clauses.schemas import Clause, ClauseVariant
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.record import DocumentRecord
from tmis.document_intelligence.storage.in_memory_store import InMemoryDocumentStore

_RISKY_CLAUSE = Clause(
    id="clause-risk",
    domain=LegalDomain.COMMERCIAL,
    clause_type="limitation_responsabilite",
    title="Clause de limitation de responsabilité",
    variants=(
        ClauseVariant(
            id="variant-risk",
            text="La responsabilité du prestataire est totalement exclue en toute circonstance",
            notes="Variante à risque : exclusion totale défavorable au client",
        ),
    ),
    jurisprudence_refs=("Cass. com., 1 fevrier 2011",),
)

_STANDARD_CLAUSE = Clause(
    id="clause-std",
    domain=LegalDomain.COMMERCIAL,
    clause_type="confidentialite",
    title="Clause de confidentialité",
    variants=(
        ClauseVariant(
            id="variant-std",
            text="Les parties s'engagent a garder confidentielles les informations echangees",
            notes="Variante standard du cabinet",
        ),
    ),
)

_MISSING_CLAUSE = Clause(
    id="clause-missing",
    domain=LegalDomain.COMMERCIAL,
    clause_type="clause_resiliation",
    title="Clause de résiliation anticipée",
    variants=(ClauseVariant(id="variant-missing", text="Resiliation possible avec preavis"),),
)


class _FakeClauseEngine:
    def __init__(self, clauses: list[Clause] | None = None) -> None:
        self._clauses = clauses if clauses is not None else [
            _RISKY_CLAUSE,
            _STANDARD_CLAUSE,
            _MISSING_CLAUSE,
        ]
        self.seen_domains: list[LegalDomain | None] = []

    def search(
        self,
        firm_id: str,
        domain: LegalDomain | None = None,
        clause_type: str | None = None,
        keyword: str | None = None,
    ) -> list[Clause]:
        self.seen_domains.append(domain)
        return list(self._clauses)


def _make_document(document_id: str = "doc-1", ocr_text: str | None = None) -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        filename="contrat-prestation.pdf",
        status=ProcessingStatus.STORED,
        raw_bytes=b"%PDF-1.4 fake",
        ocr_text=ocr_text
        or (
            "Contrat de prestation de services.\n\n"
            "Clause de limitation de responsabilité : "
            "la responsabilite du prestataire est totalement exclue en toute circonstance.\n\n"
            "Clause de confidentialité : "
            "les parties s'engagent a garder confidentielles les informations echangees."
        ),
    )


@pytest.mark.asyncio
async def test_contract_agent_without_document_id_is_low_confidence() -> None:
    agent = ContractAgent()
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=None)

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert output.result["clauses"] == []
    assert output.result["version_diff"] is None
    assert any("No document_id" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_contract_agent_reports_missing_document() -> None:
    agent = ContractAgent(document_store=InMemoryDocumentStore())
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"document_id": "missing-doc"}
    )

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert any("missing-doc" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_contract_agent_detects_risky_and_missing_clauses() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)
    clause_engine = _FakeClauseEngine()

    agent = ContractAgent(document_store=document_store, clause_engine=clause_engine)
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"document_id": document.document_id}
    )

    output = await agent.run(agent_input)

    findings = {f["clause_id"]: f for f in output.result["clauses"]}
    assert findings["clause-risk"]["status"] == "present"
    assert "risque" in findings["clause-risk"]["risk_notes"].lower()
    assert findings["clause-std"]["status"] == "present"
    assert findings["clause-std"]["risk_notes"] is None
    assert findings["clause-missing"]["status"] == "missing"
    assert findings["clause-missing"]["risk_notes"] is None
    assert clause_engine.seen_domains == [LegalDomain.COMMERCIAL]
    assert output.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)
    assert output.citations[0].source_id == document.document_id


@pytest.mark.asyncio
async def test_contract_agent_resolves_domain_from_context() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)
    clause_engine = _FakeClauseEngine()

    agent = ContractAgent(document_store=document_store, clause_engine=clause_engine)
    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=None,
        context={"document_id": document.document_id, "domain": "social"},
    )

    await agent.run(agent_input)

    assert clause_engine.seen_domains == [LegalDomain.SOCIAL]


@pytest.mark.asyncio
async def test_contract_agent_low_confidence_when_library_is_empty() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)
    clause_engine = _FakeClauseEngine(clauses=[])

    agent = ContractAgent(document_store=document_store, clause_engine=clause_engine)
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"document_id": document.document_id}
    )

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert any("No clause found" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_contract_agent_generates_a_synthesis_without_a_fabric() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)

    agent = ContractAgent(document_store=document_store, clause_engine=_FakeClauseEngine())
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"document_id": document.document_id}
    )

    output = await agent.run(agent_input)

    assert output.result["synthesis"]
    assert output.result["model"] == "default"


@pytest.mark.asyncio
async def test_contract_agent_routes_synthesis_through_the_fabric() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)

    agent = ContractAgent(
        document_store=document_store,
        clause_engine=_FakeClauseEngine(),
        fabric=get_ai_intelligence_fabric(),
        firm_id="firm-test",
    )
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"document_id": document.document_id}
    )

    output = await agent.run(agent_input)

    assert output.result["synthesis"]
    assert output.result["model"] != "default"


@pytest.mark.asyncio
async def test_contract_agent_uses_case_profile_when_case_id_is_known() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)
    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    case_store.save(CaseProfile(case_id=case_id, title="Prestataire c/ Client"))

    agent = ContractAgent(
        document_store=document_store, case_store=case_store, clause_engine=_FakeClauseEngine()
    )
    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=uuid.UUID(case_id),
        context={"document_id": document.document_id},
    )

    output = await agent.run(agent_input)

    assert not any("was not found in the case store" in warning for warning in output.warnings)
    assert output.result["synthesis"]


@pytest.mark.asyncio
async def test_contract_agent_warns_when_case_id_not_found() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)
    missing_case_id = uuid.uuid4()

    agent = ContractAgent(
        document_store=document_store,
        case_store=InMemoryCaseStore(),
        clause_engine=_FakeClauseEngine(),
    )
    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=missing_case_id,
        context={"document_id": document.document_id},
    )

    output = await agent.run(agent_input)

    assert any(str(missing_case_id) in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_contract_agent_compares_two_documents_when_asked() -> None:
    document_store = InMemoryDocumentStore()
    original = _make_document(
        document_id="doc-v1",
        ocr_text="Article 1 : Objet du contrat.\n\nArticle 2 : Duree de douze mois.",
    )
    revised = _make_document(
        document_id="doc-v2",
        ocr_text=(
            "Article 1 : Objet du contrat.\n\n"
            "Article 2 : Duree de vingt-quatre mois.\n\n"
            "Article 3 : Confidentialite."
        ),
    )
    document_store.save(original)
    document_store.save(revised)

    agent = ContractAgent(document_store=document_store, clause_engine=_FakeClauseEngine())
    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=None,
        context={"document_id": original.document_id, "compare_document_id": revised.document_id},
    )

    output = await agent.run(agent_input)

    diff = output.result["version_diff"]
    assert diff is not None
    assert any("vingt-quatre" in entry["after"] for entry in diff["changed_paragraphs"])
    assert any("Confidentialite" in p for p in diff["added_paragraphs"])
    assert len(output.citations) == 2


@pytest.mark.asyncio
async def test_contract_agent_warns_when_compare_document_not_found() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)

    agent = ContractAgent(document_store=document_store, clause_engine=_FakeClauseEngine())
    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=None,
        context={"document_id": document.document_id, "compare_document_id": "missing-doc"},
    )

    output = await agent.run(agent_input)

    assert output.result["version_diff"] is None
    assert any("missing-doc" in warning for warning in output.warnings)
    assert len(output.citations) == 1


@pytest.mark.asyncio
async def test_contract_agent_records_explainability_when_governance_is_wired() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)
    governance = get_ai_governance_platform()
    task_id = uuid.uuid4()

    agent = ContractAgent(
        document_store=document_store,
        clause_engine=_FakeClauseEngine(),
        governance=governance,
        firm_id="firm-explainability",
    )
    agent_input = AgentInput(
        task_id=task_id, case_id=None, context={"document_id": document.document_id}
    )

    await agent.run(agent_input)

    report = governance.explainability.latest("firm-explainability", str(task_id))
    assert report is not None
    assert document.document_id in report.documents_consulted
    assert any("Synthèse de risques générée" in step for step in report.steps_followed)
