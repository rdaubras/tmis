import time
import uuid

from tmis.ai.events.bus import EventBus
from tmis.ai.events.events import (
    ArgumentAdded,
    ConfidenceCalculated,
    ConflictDetected,
    CounterArgumentAdded,
    HypothesisCreated,
    ReasoningCompleted,
    ReasoningStarted,
)
from tmis.ai.kernel import TMISKernel
from tmis.core.logging import get_logger
from tmis.legal_reasoning.arguments.engine import HeuristicArgumentEngine
from tmis.legal_reasoning.arguments.ports import ArgumentEnginePort
from tmis.legal_reasoning.confidence.engine import ConfigurableConfidenceEngine
from tmis.legal_reasoning.confidence.ports import ConfidenceEnginePort
from tmis.legal_reasoning.confidence.schemas import ConfidenceScore, ConfidenceWeights
from tmis.legal_reasoning.conflicts.engine import HeuristicConflictDetector
from tmis.legal_reasoning.conflicts.ports import ConflictDetectorPort
from tmis.legal_reasoning.conflicts.schemas import Conflict
from tmis.legal_reasoning.counter_arguments.engine import HeuristicCounterArgumentEngine
from tmis.legal_reasoning.counter_arguments.ports import CounterArgumentEnginePort
from tmis.legal_reasoning.decision_graph.builder import ChainDecisionGraphBuilder
from tmis.legal_reasoning.decision_graph.ports import DecisionGraphBuilderPort
from tmis.legal_reasoning.evaluation.evaluator import ReasoningEvaluator
from tmis.legal_reasoning.evaluation.metrics import ReasoningMetrics
from tmis.legal_reasoning.evidence.engine import HeuristicEvidenceEngine
from tmis.legal_reasoning.evidence.ports import EvidenceEnginePort
from tmis.legal_reasoning.explanations.engine import ReasoningExplanationEngine
from tmis.legal_reasoning.explanations.ports import ExplanationEnginePort
from tmis.legal_reasoning.hypotheses.engine import HeuristicHypothesisEngine
from tmis.legal_reasoning.hypotheses.ports import HypothesisEnginePort
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_reasoning.planner.planner import HeuristicReasoningPlanner
from tmis.legal_reasoning.planner.ports import ReasoningPlannerPort
from tmis.legal_reasoning.reasoner.in_memory_store import InMemorySessionStore
from tmis.legal_reasoning.reasoner.ports import (
    ReasoningCasePort,
    ReasoningKernelPort,
    ReasoningResearchPort,
    SessionStorePort,
)
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_reasoning.strategy.engine import HeuristicStrategyEngine
from tmis.legal_reasoning.strategy.ports import StrategyEnginePort

_LOGGER_NAME = "tmis.legal_reasoning.reasoner"


class ReasoningOrchestrator:
    """Pilots one full reasoning run (see docs/25-legal-reasoning.md):
    question -> case analysis -> documentary research -> fact extraction
    -> hypotheses -> arguments -> counter-arguments -> evidence -> confidence
    -> conflicts -> synthesis. Every dependency is injected behind a port
    with a heuristic default, matching the `CaseIntelligenceWorkflow`/
    `ResearchOrchestrator` pattern from Sprints 4-5. It never produces a
    final legal document or an automatic legal conclusion — `synthesis`
    is a transparent summary of the reasoning, always framed as such.
    """

    def __init__(
        self,
        *,
        case_port: ReasoningCasePort,
        research_port: ReasoningResearchPort,
        kernel: ReasoningKernelPort | None = None,
        planner: ReasoningPlannerPort | None = None,
        hypothesis_engine: HypothesisEnginePort | None = None,
        argument_engine: ArgumentEnginePort | None = None,
        counter_argument_engine: CounterArgumentEnginePort | None = None,
        evidence_engine: EvidenceEnginePort | None = None,
        confidence_engine: ConfidenceEnginePort | None = None,
        conflict_detector: ConflictDetectorPort | None = None,
        strategy_engine: StrategyEnginePort | None = None,
        explanation_engine: ExplanationEnginePort | None = None,
        decision_graph_builder: DecisionGraphBuilderPort | None = None,
        event_bus: EventBus | None = None,
        evaluator: ReasoningEvaluator | None = None,
        confidence_weights: ConfidenceWeights | None = None,
        session_store: SessionStorePort | None = None,
    ) -> None:
        self._case_port = case_port
        self._research_port = research_port
        self._kernel: ReasoningKernelPort = kernel or TMISKernel()
        self._planner = planner or HeuristicReasoningPlanner()
        self._hypothesis_engine = hypothesis_engine or HeuristicHypothesisEngine()
        self._argument_engine = argument_engine or HeuristicArgumentEngine()
        self._counter_argument_engine = counter_argument_engine or HeuristicCounterArgumentEngine()
        self._evidence_engine = evidence_engine or HeuristicEvidenceEngine()
        self._confidence_engine = confidence_engine or ConfigurableConfidenceEngine()
        self._conflict_detector = conflict_detector or HeuristicConflictDetector()
        self._strategy_engine = strategy_engine or HeuristicStrategyEngine()
        self._explanation_engine = explanation_engine or ReasoningExplanationEngine()
        self._decision_graph_builder = decision_graph_builder or ChainDecisionGraphBuilder()
        self.event_bus = event_bus or EventBus()
        self._evaluator = evaluator or ReasoningEvaluator()
        self._confidence_weights = confidence_weights
        self._logger = get_logger(_LOGGER_NAME)
        self._session_store: SessionStorePort = session_store or InMemorySessionStore()

    async def reason(self, question: str, *, case_id: str | None = None) -> ReasoningSession:
        start = time.perf_counter()
        session_id = str(uuid.uuid4())
        workflow_id = uuid.uuid4()
        modules_used: list[str] = []

        await self.event_bus.publish(
            ReasoningStarted(
                workflow_id=workflow_id, session_id=session_id, question=question, case_id=case_id
            )
        )
        self._planner.build_plan(question, case_id)

        profile = self._case_port.get_profile(case_id) if case_id else None
        modules_used.append("case_intelligence")
        facts = profile.facts if profile else []
        timeline_inconsistencies = profile.timeline_inconsistencies if profile else []

        research_response = await self._research_port.search(question, case_id=case_id)
        modules_used.append("legal_research")
        research_results = list(research_response.results)

        hypotheses = self._hypothesis_engine.generate(question, facts, research_results)
        modules_used.append("hypotheses")
        for hypothesis in hypotheses:
            await self.event_bus.publish(
                HypothesisCreated(
                    workflow_id=workflow_id, session_id=session_id, hypothesis_id=hypothesis.id
                )
            )

        arguments = self._argument_engine.build(hypotheses, research_results)
        modules_used.append("arguments")
        for argument in arguments:
            await self.event_bus.publish(
                ArgumentAdded(
                    workflow_id=workflow_id,
                    session_id=session_id,
                    argument_id=argument.id,
                    hypothesis_id=argument.hypothesis_id,
                )
            )

        counter_arguments = self._counter_argument_engine.build(
            arguments, hypotheses, facts, research_results
        )
        modules_used.append("counter_arguments")
        for counter in counter_arguments:
            await self.event_bus.publish(
                CounterArgumentAdded(
                    workflow_id=workflow_id,
                    session_id=session_id,
                    counter_argument_id=counter.id,
                    argument_id=counter.argument_id,
                )
            )

        evidence_links = self._evidence_engine.link(hypotheses, arguments, facts)
        modules_used.append("evidence")

        confidence_scores: dict[str, ConfidenceScore] = {}
        for hypothesis in hypotheses:
            score = self._confidence_engine.score(
                hypothesis, arguments, counter_arguments, evidence_links, self._confidence_weights
            )
            confidence_scores[hypothesis.id] = score
            hypothesis.confidence = score.value
            await self.event_bus.publish(
                ConfidenceCalculated(
                    workflow_id=workflow_id,
                    session_id=session_id,
                    hypothesis_id=hypothesis.id,
                    value=score.value,
                )
            )
        modules_used.append("confidence")

        conflicts = self._conflict_detector.detect(facts, timeline_inconsistencies)
        modules_used.append("conflicts")
        for conflict in conflicts:
            await self.event_bus.publish(
                ConflictDetected(
                    workflow_id=workflow_id,
                    session_id=session_id,
                    conflict_id=conflict.id,
                    conflict_type=conflict.type.value,
                )
            )

        strategies = self._strategy_engine.propose(
            hypotheses, arguments, counter_arguments, conflicts, confidence_scores
        )
        modules_used.append("strategy")

        synthesis = await self._build_synthesis(question, hypotheses, confidence_scores, conflicts)
        modules_used.append("synthesis")

        references = sorted({a.source_reference for a in arguments})
        explanation = self._explanation_engine.build(
            question, hypotheses, arguments, counter_arguments, conflicts, confidence_scores
        )
        modules_used.append("explanations")
        decision_graph = self._decision_graph_builder.build(
            question,
            hypotheses,
            arguments,
            counter_arguments,
            evidence_links,
            references,
            synthesis,
        )
        modules_used.append("decision_graph")

        duration_ms = (time.perf_counter() - start) * 1000
        session = ReasoningSession(
            id=session_id,
            question=question,
            case_id=case_id,
            hypotheses=hypotheses,
            arguments=arguments,
            counter_arguments=counter_arguments,
            evidence_links=evidence_links,
            conflicts=conflicts,
            confidence_scores=confidence_scores,
            strategies=strategies,
            synthesis=synthesis,
            explanation=explanation,
            decision_graph=decision_graph,
            duration_ms=duration_ms,
        )
        self._session_store.save(session)

        average_confidence = (
            sum(s.value for s in confidence_scores.values()) / len(confidence_scores)
            if confidence_scores
            else 0.0
        )
        self._evaluator.record(
            ReasoningMetrics(
                session_id=session_id,
                duration_ms=duration_ms,
                modules_used=tuple(modules_used),
                average_confidence=average_confidence,
                hypothesis_count=len(hypotheses),
                argument_count=len(arguments),
                counter_argument_count=len(counter_arguments),
                conflict_count=len(conflicts),
            )
        )
        self._logger.info(
            "reasoning_completed",
            session_id=session_id,
            duration_ms=duration_ms,
            hypothesis_count=len(hypotheses),
            conflict_count=len(conflicts),
            average_confidence=average_confidence,
        )
        await self.event_bus.publish(
            ReasoningCompleted(
                workflow_id=workflow_id,
                session_id=session_id,
                hypothesis_count=len(hypotheses),
                conflict_count=len(conflicts),
                duration_ms=duration_ms,
            )
        )
        return session

    async def _build_synthesis(
        self,
        question: str,
        hypotheses: list[Hypothesis],
        confidence_scores: dict[str, ConfidenceScore],
        conflicts: list[Conflict],
    ) -> str:
        hypotheses_summary = "; ".join(
            f"{h.description} (confiance {confidence_scores[h.id].value:.2f})" for h in hypotheses
        )
        conflicts_summary = (
            f"{len(conflicts)} conflit(s) détecté(s) dans le dossier."
            if conflicts
            else "Aucun conflit détecté."
        )
        prompt = (
            f"Rédige une synthèse transparente et prudente du raisonnement suivant pour la "
            f"question « {question} », sans jamais formuler de conclusion juridique définitive : "
            f"hypothèses envisagées : {hypotheses_summary}. {conflicts_summary} "
            "Rappelle que cette synthèse doit être validée par un avocat."
        )
        response = await self._kernel.complete(prompt)
        return response.text

    def get_session(self, session_id: str) -> ReasoningSession | None:
        return self._session_store.get(session_id)
