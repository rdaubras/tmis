from fastapi import APIRouter, Depends, HTTPException

from tmis.legal_reasoning.api.schemas import (
    ArgumentResponse,
    ConfidenceScoreResponse,
    ConflictResponse,
    CounterArgumentResponse,
    DecisionEdgeResponse,
    DecisionGraphResponse,
    DecisionNodeResponse,
    ExplanationResponse,
    HypothesisResponse,
    ReasoningRequest,
    ReasoningSessionResponse,
    StrategyOptionResponse,
)
from tmis.legal_reasoning.bootstrap import get_reasoning_orchestrator
from tmis.legal_reasoning.reasoner.orchestrator import ReasoningOrchestrator
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession

router = APIRouter(prefix="/legal-reasoning", tags=["legal-reasoning"])


def _to_session_response(session: ReasoningSession) -> ReasoningSessionResponse:
    return ReasoningSessionResponse(
        id=session.id,
        question=session.question,
        case_id=session.case_id,
        hypotheses=[
            HypothesisResponse(
                id=h.id,
                description=h.description,
                supporting_fact_ids=list(h.supporting_fact_ids),
                references=list(h.references),
                confidence=h.confidence,
                status=h.status.value,
            )
            for h in session.hypotheses
        ],
        arguments=[
            ArgumentResponse(
                id=a.id,
                hypothesis_id=a.hypothesis_id,
                claim=a.claim,
                source_connector=a.source_connector,
                source_reference=a.source_reference,
                excerpt=a.excerpt,
                confidence=a.confidence,
            )
            for a in session.arguments
        ],
        counter_arguments=[
            CounterArgumentResponse(
                id=c.id,
                argument_id=c.argument_id,
                claim=c.claim,
                source_connector=c.source_connector,
                source_reference=c.source_reference,
                excerpt=c.excerpt,
                confidence=c.confidence,
            )
            for c in session.counter_arguments
        ],
        conflicts=[
            ConflictResponse(
                id=c.id,
                type=c.type.value,
                description=c.description,
                explanation=c.explanation,
                involved_ids=list(c.involved_ids),
            )
            for c in session.conflicts
        ],
        confidence_scores=[
            ConfidenceScoreResponse(
                hypothesis_id=s.hypothesis_id,
                value=s.value,
                explanation=s.explanation,
                factors=s.factors,
            )
            for s in session.confidence_scores.values()
        ],
        strategies=[
            StrategyOptionResponse(
                id=s.id,
                hypothesis_id=s.hypothesis_id,
                objective=s.objective,
                favorable_points=list(s.favorable_points),
                risks=list(s.risks),
                missing_elements=list(s.missing_elements),
            )
            for s in session.strategies
        ],
        synthesis=session.synthesis,
        explanation=(
            ExplanationResponse(
                reasoning_steps=list(session.explanation.reasoning_steps),
                components_used=list(session.explanation.components_used),
                references=list(session.explanation.references),
                hypotheses_considered=list(session.explanation.hypotheses_considered),
                limitations=list(session.explanation.limitations),
            )
            if session.explanation is not None
            else None
        ),
        decision_graph=(
            DecisionGraphResponse(
                nodes=[
                    DecisionNodeResponse(id=n.id, type=n.type.value, label=n.label)
                    for n in session.decision_graph.nodes
                ],
                edges=[
                    DecisionEdgeResponse(
                        source_id=e.source_id, target_id=e.target_id, relation=e.relation
                    )
                    for e in session.decision_graph.edges
                ],
            )
            if session.decision_graph is not None
            else None
        ),
        duration_ms=session.duration_ms,
        created_at=session.created_at,
    )


def _get_session_or_404(
    session_id: str, orchestrator: ReasoningOrchestrator
) -> ReasoningSession:
    session = orchestrator.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=404, detail=f"No reasoning session found for {session_id!r}"
        )
    return session


@router.post("/reason", response_model=ReasoningSessionResponse)
async def launch_reasoning(
    payload: ReasoningRequest,
    orchestrator: ReasoningOrchestrator = Depends(get_reasoning_orchestrator),
) -> ReasoningSessionResponse:
    session = await orchestrator.reason(payload.question, case_id=payload.case_id)
    return _to_session_response(session)


@router.get("/sessions/{session_id}", response_model=ReasoningSessionResponse)
def get_session(
    session_id: str,
    orchestrator: ReasoningOrchestrator = Depends(get_reasoning_orchestrator),
) -> ReasoningSessionResponse:
    return _to_session_response(_get_session_or_404(session_id, orchestrator))


@router.get("/sessions/{session_id}/hypotheses", response_model=list[HypothesisResponse])
def get_hypotheses(
    session_id: str,
    orchestrator: ReasoningOrchestrator = Depends(get_reasoning_orchestrator),
) -> list[HypothesisResponse]:
    return _to_session_response(_get_session_or_404(session_id, orchestrator)).hypotheses


@router.get("/sessions/{session_id}/arguments", response_model=list[ArgumentResponse])
def get_arguments(
    session_id: str,
    orchestrator: ReasoningOrchestrator = Depends(get_reasoning_orchestrator),
) -> list[ArgumentResponse]:
    return _to_session_response(_get_session_or_404(session_id, orchestrator)).arguments


@router.get("/sessions/{session_id}/conflicts", response_model=list[ConflictResponse])
def get_conflicts(
    session_id: str,
    orchestrator: ReasoningOrchestrator = Depends(get_reasoning_orchestrator),
) -> list[ConflictResponse]:
    return _to_session_response(_get_session_or_404(session_id, orchestrator)).conflicts


@router.get("/sessions/{session_id}/synthesis")
def get_synthesis(
    session_id: str,
    orchestrator: ReasoningOrchestrator = Depends(get_reasoning_orchestrator),
) -> dict[str, str]:
    session = _get_session_or_404(session_id, orchestrator)
    return {"synthesis": session.synthesis}
