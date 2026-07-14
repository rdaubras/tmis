import uuid

import pytest

from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.agents.synthesis_agent import SynthesisAgent
from tmis.ai_fabric.bootstrap import get_ai_intelligence_fabric
from tmis.ai_governance.bootstrap import get_ai_governance_platform
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.writing_style.engine import WritingStyleEngine
from tmis.case_intelligence.actors.schemas import Actor, ActorType, CaseActorRole
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.schemas import CaseProfile, CaseTask
from tmis.case_intelligence.facts.schemas import Fact
from tmis.case_intelligence.issues.schemas import LegalIssue
from tmis.case_intelligence.summaries.schemas import CaseSummary
from tmis.case_intelligence.timeline.schemas import CaseTimelineEntry, TimelineInconsistency


def _make_case_profile(case_id: str = "case-1") -> CaseProfile:
    actor = Actor(id="actor-1", type=ActorType.PERSON, name="Jean Dupont")
    return CaseProfile(
        case_id=case_id,
        title="Dupont c/ Acme",
        actors=[actor],
        actor_roles={"actor-1": CaseActorRole.CLIENT},
        document_ids={"doc-1"},
        timeline=[
            CaseTimelineEntry(
                date="2024-03-12",
                description="Signature du bail",
                document_ids=("doc-1",),
                confidence=0.9,
            )
        ],
        facts=[Fact(id="fact-1", description="Bail signe", confidence=0.8, dates=("2024-03-12",))],
        legal_issues=[LegalIssue(id="issue-1", description="Validite de la clause resolutoire")],
        tasks=[
            CaseTask(id="task-1", description="Deposer les conclusions", done=False),
            CaseTask(id="task-2", description="Notifier l'assignation", done=True),
        ],
    )


@pytest.mark.asyncio
async def test_synthesis_agent_without_case_id_is_low_confidence() -> None:
    agent = SynthesisAgent()
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=None)

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert any("case_id" in warning for warning in output.warnings)
    assert output.result["table"] == {"actors": [], "facts": [], "deadlines": []}


@pytest.mark.asyncio
async def test_synthesis_agent_reports_missing_case() -> None:
    agent = SynthesisAgent(case_store=InMemoryCaseStore())
    missing_case_id = uuid.uuid4()
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=missing_case_id)

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert any(str(missing_case_id) in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_synthesis_agent_reuses_case_summary_generator_for_executive_summary() -> None:
    class _RecordingSummaryGenerator:
        def __init__(self) -> None:
            self.profiles_seen: list[CaseProfile] = []

        async def generate(self, profile: CaseProfile) -> CaseSummary:
            self.profiles_seen.append(profile)
            return CaseSummary(
                executive_summary="[recorded] resume",
                chronological_summary="chrono",
                documentary_summary="docs",
                case_status="En cours",
                open_points=("point ouvert",),
            )

    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    profile = _make_case_profile(case_id=case_id)
    case_store.save(profile)

    summary_generator = _RecordingSummaryGenerator()
    agent = SynthesisAgent(case_store=case_store, summary_generator=summary_generator)
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=uuid.UUID(case_id))

    output = await agent.run(agent_input)

    assert summary_generator.profiles_seen == [profile]
    assert output.result["executive_summary"] == "[recorded] resume"
    assert output.result["chronological_summary"] == "chrono"
    assert output.result["open_points"] == ["point ouvert"]


@pytest.mark.asyncio
async def test_synthesis_agent_produces_table_fact_sheet_and_checklist() -> None:
    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    profile = _make_case_profile(case_id=case_id)
    case_store.save(profile)

    agent = SynthesisAgent(case_store=case_store)
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=uuid.UUID(case_id))

    output = await agent.run(agent_input)

    assert output.result["executive_summary"]
    assert "2024-03-12" in output.result["chronological_summary"]

    table = output.result["table"]
    assert [a["name"] for a in table["actors"]] == ["Jean Dupont"]
    assert table["actors"][0]["role"] == "client"
    assert [f["description"] for f in table["facts"]] == ["Bail signe"]
    assert [d["description"] for d in table["deadlines"]] == ["Deposer les conclusions"]

    fact_sheet = output.result["fact_sheet"]
    assert fact_sheet["title"] == "Dupont c/ Acme"
    assert fact_sheet["clients"] == ["Jean Dupont"]
    assert fact_sheet["document_count"] == 1
    assert fact_sheet["open_issue_count"] == 1

    checklist = output.result["checklist"]
    items = {(entry["item"], entry["done"]) for entry in checklist}
    assert ("Validite de la clause resolutoire", False) in items
    assert ("Deposer les conclusions", False) in items
    assert ("Notifier l'assignation", True) in items

    assert output.result["synthesis_note"]
    assert output.citations[0].source_id == case_id
    assert output.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)


@pytest.mark.asyncio
async def test_synthesis_agent_surfaces_timeline_inconsistencies_via_open_points() -> None:
    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    profile = _make_case_profile(case_id=case_id)
    profile.timeline_inconsistencies = [
        TimelineInconsistency(
            date="2024-03-12",
            entries=(
                profile.timeline[0],
                CaseTimelineEntry(
                    date="2024-03-12",
                    description="Resiliation anticipee",
                    document_ids=("doc-2",),
                    confidence=0.6,
                ),
            ),
        )
    ]
    case_store.save(profile)

    agent = SynthesisAgent(case_store=case_store)
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=uuid.UUID(case_id))

    output = await agent.run(agent_input)

    assert any("2024-03-12" in point for point in output.result["open_points"])
    assert any(
        entry["item"] == next(
            point for point in output.result["open_points"] if "2024-03-12" in point
        )
        for entry in output.result["checklist"]
    )


@pytest.mark.asyncio
async def test_synthesis_agent_injects_writing_style_profile_into_prompt() -> None:
    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    case_store.save(_make_case_profile(case_id=case_id))

    knowledge_space = KnowledgeSpace(InMemoryKnowledgeStore())
    style_engine = WritingStyleEngine(knowledge_space)
    style_engine.update_profile(
        "firm-style-test",
        "avocat1",
        vocabulary=("nonobstant",),
        favorite_expressions=("il convient de rappeler",),
    )

    agent = SynthesisAgent(
        case_store=case_store,
        writing_style_engine=style_engine,
        firm_id="firm-style-test",
    )
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=uuid.UUID(case_id))

    output = await agent.run(agent_input)

    assert output.result["synthesis_note"]


@pytest.mark.asyncio
async def test_synthesis_agent_routes_model_through_fabric() -> None:
    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    case_store.save(_make_case_profile(case_id=case_id))

    agent = SynthesisAgent(
        case_store=case_store, fabric=get_ai_intelligence_fabric(), firm_id="firm-test"
    )
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=uuid.UUID(case_id))

    output = await agent.run(agent_input)

    assert output.result["model"] != "default"


@pytest.mark.asyncio
async def test_synthesis_agent_medium_confidence_when_timeline_inconsistencies_reported() -> None:
    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    profile = _make_case_profile(case_id=case_id)
    profile.timeline_inconsistencies = [
        TimelineInconsistency(
            date="2024-03-12",
            entries=(
                profile.timeline[0],
                CaseTimelineEntry(
                    date="2024-03-12",
                    description="Resiliation anticipee",
                    document_ids=("doc-2",),
                    confidence=0.6,
                ),
            ),
        )
    ]
    case_store.save(profile)

    agent = SynthesisAgent(case_store=case_store)
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=uuid.UUID(case_id))

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.MEDIUM
    assert any("timeline inconsistency" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_synthesis_agent_low_confidence_when_case_has_no_data() -> None:
    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    case_store.save(CaseProfile(case_id=case_id, title="Dossier vide"))

    agent = SynthesisAgent(case_store=case_store)
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=uuid.UUID(case_id))

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert any("no actors, facts, or timeline entries" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_synthesis_agent_prompt_includes_structure_preferences() -> None:
    knowledge_space = KnowledgeSpace(InMemoryKnowledgeStore())
    style_engine = WritingStyleEngine(knowledge_space)
    style_engine.update_profile(
        "firm-structure-test",
        "avocat1",
        structure_preferences=("plan en trois parties",),
    )

    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    case_store.save(_make_case_profile(case_id=case_id))

    agent = SynthesisAgent(
        case_store=case_store,
        writing_style_engine=style_engine,
        firm_id="firm-structure-test",
    )
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=uuid.UUID(case_id))

    output = await agent.run(agent_input)

    assert output.result["synthesis_note"]


@pytest.mark.asyncio
async def test_synthesis_agent_records_explainability() -> None:
    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    case_store.save(_make_case_profile(case_id=case_id))

    governance = get_ai_governance_platform()
    agent = SynthesisAgent(
        case_store=case_store,
        governance=governance,
        firm_id="firm-explainability-synthesis-test",
    )
    task_id = uuid.uuid4()
    agent_input = AgentInput(task_id=task_id, case_id=uuid.UUID(case_id))

    await agent.run(agent_input)

    report = governance.explainability.latest("firm-explainability-synthesis-test", str(task_id))
    assert report is not None
    assert any("dossier" in step for step in report.steps_followed)
    assert "synthesis" in report.agents_involved
