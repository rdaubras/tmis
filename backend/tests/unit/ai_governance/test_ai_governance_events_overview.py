import pytest

from tmis.ai_governance.decision_records.engine import DecisionRecordEngine
from tmis.ai_governance.decision_records.store import InMemoryDecisionRecordStore
from tmis.ai_governance.events import DecisionRecorded, GovernanceEventBus
from tmis.ai_governance.explainability.engine import ExplainabilityEngine
from tmis.ai_governance.explainability.store import InMemoryExplainabilityStore
from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.store import InMemoryValidationStore
from tmis.ai_governance.lineage.engine import LineageEngine
from tmis.ai_governance.lineage.store import InMemoryLineageStore
from tmis.ai_governance.overview import AIGovernancePlatform
from tmis.ai_governance.provenance.engine import ProvenanceEngine
from tmis.ai_governance.provenance.schemas import ProvenanceGranularity, SourceType
from tmis.ai_governance.provenance.store import InMemoryProvenanceStore
from tmis.ai_governance.reasoning_chain.engine import ReasoningChainEngine
from tmis.ai_governance.reasoning_chain.schemas import ChainStageType
from tmis.ai_governance.reasoning_chain.store import InMemoryReasoningChainStore
from tmis.ai_governance.traceability.engine import TraceabilityEngine
from tmis.ai_governance.traceability.store import InMemoryTraceStore

FIRM = "firm-a"
PRODUCTION = "prod-1"


@pytest.mark.asyncio
async def test_governance_event_bus_publishes_and_records_history() -> None:
    bus = GovernanceEventBus()
    received: list[DecisionRecorded] = []

    async def _handler(event: DecisionRecorded) -> None:
        received.append(event)

    bus.subscribe(DecisionRecorded, _handler)
    event = DecisionRecorded(firm_id=FIRM, decision_record_id="dec-1")
    await bus.publish(event)

    assert received == [event]
    assert bus.history == [event]


@pytest.mark.asyncio
async def test_governance_event_bus_unsubscribe_stops_delivery() -> None:
    bus = GovernanceEventBus()
    received: list[DecisionRecorded] = []

    async def _handler(event: DecisionRecorded) -> None:
        received.append(event)

    bus.subscribe(DecisionRecorded, _handler)
    bus.unsubscribe(DecisionRecorded, _handler)
    await bus.publish(DecisionRecorded(firm_id=FIRM, decision_record_id="dec-1"))

    assert received == []


def _platform() -> AIGovernancePlatform:
    return AIGovernancePlatform(
        ReasoningChainEngine(InMemoryReasoningChainStore()),
        ProvenanceEngine(InMemoryProvenanceStore()),
        TraceabilityEngine(InMemoryTraceStore()),
        DecisionRecordEngine(InMemoryDecisionRecordStore()),
        HumanValidationEngine(InMemoryValidationStore()),
        LineageEngine(InMemoryLineageStore()),
        ExplainabilityEngine(InMemoryExplainabilityStore()),
    )


def test_overview_of_untouched_production_returns_empty_but_valid_structures() -> None:
    platform = _platform()

    overview = platform.overview(FIRM, "unknown-production")

    assert overview.reasoning_chain.steps == []
    assert overview.provenance == ()
    assert overview.trace == ()
    assert overview.decisions == ()
    assert overview.validations == ()
    assert overview.explainability is None
    assert overview.confidence is None


def test_overview_composes_every_persisted_engine() -> None:
    platform = _platform()

    platform.reasoning_chain.record_step(
        FIRM, PRODUCTION, ChainStageType.QUESTION, "Le bail est-il résiliable ?"
    )
    platform.provenance.record(
        FIRM,
        PRODUCTION,
        granularity=ProvenanceGranularity.PARAGRAPH,
        locator="para-1",
        excerpt="Art. 1103",
        source_type=SourceType.STATUTE_ARTICLE,
        source_reference="Code civil art. 1103",
    )
    platform.traceability.record_user(FIRM, PRODUCTION, "user-1")
    platform.decision_records.record(
        FIRM,
        PRODUCTION,
        context="c",
        objective="o",
        decision="d",
        justification="j",
    )
    platform.human_validation.request_simple(FIRM, PRODUCTION, "user-1", ("approver-1",))
    platform.lineage.record_origin(FIRM, PRODUCTION, ("doc-1",), "user-1")
    platform.explainability.generate(
        FIRM, PRODUCTION, summary="Résumé", steps_followed=("Question",)
    )

    overview = platform.overview(FIRM, PRODUCTION)

    assert len(overview.reasoning_chain.steps) == 1
    assert len(overview.provenance) == 1
    assert len(overview.trace) == 1
    assert len(overview.decisions) == 1
    assert len(overview.validations) == 1
    assert overview.lineage.revision_chain == (PRODUCTION,)
    assert overview.explainability is not None
    assert overview.explainability.summary == "Résumé"


def test_overview_passes_through_caller_supplied_findings() -> None:
    platform = _platform()

    from tmis.ai_governance.confidence.schemas import GovernanceConfidenceScore

    confidence = GovernanceConfidenceScore(
        production_id=PRODUCTION, value=0.8, explanation="test", factors={}
    )

    overview = platform.overview(FIRM, PRODUCTION, confidence=confidence)

    assert overview.confidence is confidence
