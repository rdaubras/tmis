"""Watch API (Sprint 40): exposes `WatchAgent` (already real since Sprint 36,
docs/164-architecture-agent-veille.md) as a standalone `POST /watches` route —
not nested under `/cases/{case_id}` — because `WatchAgent`'s own `case_id` is
optional, exactly like `ResearchAgent`'s, and no other route in this repo
forces a folder onto an agent whose contract does not require one. See
docs/167-architecture-exposition-agent-veille.md for the full reasoning
behind this and the `POST` (over `GET` with list query params) decision.
"""

import uuid

from fastapi import APIRouter, Depends

from tmis.agents.bootstrap import get_watch_agent
from tmis.agents.contracts import AgentInput, AgentOutput
from tmis.agents.watch_agent import WatchAgent
from tmis.api.v1.watch.schemas import (
    CitationResponse,
    WatchRequest,
    WatchResponse,
    WatchResultResponse,
)

router = APIRouter(prefix="/watches", tags=["watch"])


def _to_watch_response(output: AgentOutput) -> WatchResponse:
    """`output.result` is `dict[str, object]` (the common `AgentOutput`
    contract) but its actual shape for `WatchAgent` is exactly
    `WatchResultResponse`'s fields (confirmed in Phase 0), so `model_validate`
    maps it — including the nested `new_results` list — without redeclaring
    each field name here, same pattern as `_to_analysis_response` in
    `tmis.api.v1.document.routes`."""
    return WatchResponse(
        result=WatchResultResponse.model_validate(output.result),
        citations=[
            CitationResponse(
                source_id=c.source_id,
                connector=c.connector,
                excerpt=c.excerpt,
                reference=c.reference,
            )
            for c in output.citations
        ],
        confidence=output.confidence.value,
        warnings=output.warnings,
    )


@router.post("", response_model=WatchResponse)
async def run_watch(
    payload: WatchRequest,
    watch_agent: WatchAgent = Depends(get_watch_agent),
) -> WatchResponse:
    context: dict[str, object] = {"query": payload.query}
    if payload.connectors is not None:
        context["connectors"] = payload.connectors
    if payload.known_result_ids is not None:
        context["known_result_ids"] = payload.known_result_ids

    output = await watch_agent.run(
        AgentInput(
            task_id=uuid.uuid4(),
            case_id=payload.case_id,
            context=context,
        )
    )
    return _to_watch_response(output)
