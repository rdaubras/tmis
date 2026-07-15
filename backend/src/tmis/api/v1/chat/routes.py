import dataclasses
import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from tmis.agents.bootstrap import get_research_agent
from tmis.agents.contracts import AgentInput, AgentOutput
from tmis.agents.research_agent import ResearchAgent
from tmis.ai.guardrails.exceptions import GuardrailViolation
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.ai.kernel.kernel import TMISKernel
from tmis.api.v1.chat.schemas import ChatMessageRequest
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.case_intelligence.workflow.case_workflow import CaseIntelligenceWorkflow

router = APIRouter(prefix="/chat", tags=["chat"])


def _build_prompt(history: list[str], message: str, *, case_id: str | None) -> str:
    """Reuses the `"role: content"` line format `ConversationMemory`
    already writes (see `ConversationMemory.add_message`) instead of
    inventing a second prompt convention."""
    lines = [f"[Dossier: {case_id}]", *history] if case_id is not None else list(history)
    lines.append(f"user: {message}")
    return "\n".join(lines)


def _research_agent_input(payload: ChatMessageRequest) -> AgentInput:
    """`AgentInput.case_id` is typed `uuid.UUID | None` (see
    `tmis.ai.schemas.agent`), while `ChatMessageRequest.case_id` is a
    free-form string (Sprint 32 reuses `case_intelligence`'s own,
    non-UUID-constrained case ids, see `CaseStorePort`). A case id that
    doesn't parse as a UUID is passed through as `None` here rather than
    rejecting the whole request: `ResearchOrchestrator.search()` still
    runs, it simply doesn't tag its history entry with that case."""
    case_uuid: uuid.UUID | None = None
    if payload.case_id is not None:
        try:
            case_uuid = uuid.UUID(payload.case_id)
        except ValueError:
            case_uuid = None
    return AgentInput(
        task_id=uuid.uuid4(), case_id=case_uuid, context={"query": payload.message}
    )


def _research_event_payload(output: AgentOutput) -> dict[str, object]:
    return {
        "result": output.result,
        "citations": [dataclasses.asdict(citation) for citation in output.citations],
        "confidence": output.confidence.value,
        "warnings": output.warnings,
    }


def _research_summary_text(output: AgentOutput) -> str:
    """A plain-text turn to persist in `ConversationMemory`, reusing the
    same store as the general mode so a later general-mode turn in the
    same conversation still sees this research happened (see
    `_build_prompt`) — never the raw `result`/`citations` structures,
    which `ConversationMemory` (a list of `"role: content"` strings) has
    no way to represent."""
    results = output.result.get("results")
    if not isinstance(results, list) or not results:
        return "Recherche juridique : aucun resultat trouve."
    titles = ", ".join(str(item.get("title", "")) for item in results[:3] if isinstance(item, dict))
    return f"Recherche juridique : {len(results)} resultat(s) trouve(s) ({titles})."


@router.post("/stream")
async def stream_chat(
    payload: ChatMessageRequest,
    kernel: TMISKernel = Depends(get_kernel),
    workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow),
    research_agent: ResearchAgent = Depends(get_research_agent),
) -> StreamingResponse:
    """Server-Sent Events endpoint for the chat (Sprint 32: general mode,
    `TMISKernel.complete_stream()` only; Sprint 33 adds `mode="research"`,
    additive — general mode's behavior and SSE framing are unchanged, see
    docs/160-architecture-chat-ia.md and
    docs/161-architecture-agent-recherche.md).

    Validated eagerly, before the stream starts, so a bad request still
    gets a clean 4xx: `case_id` existence (`CaseStorePort`) and the raw
    guardrail check on `message` (once headers are flushed on a
    `StreamingResponse`, an exception raised inside the generator can no
    longer become a status code — see the architecture report).
    """
    if payload.case_id is not None and workflow.case_store.get(payload.case_id) is None:
        raise HTTPException(status_code=404, detail=f"No case {payload.case_id!r}")

    try:
        kernel.guardrails.validate_input(payload.message)
    except GuardrailViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if payload.mode == "research":
        await kernel.conversation_memory.add_message(
            payload.conversation_id, "user", payload.message
        )
        output = await research_agent.run(_research_agent_input(payload))
        await kernel.conversation_memory.add_message(
            payload.conversation_id, "assistant", _research_summary_text(output)
        )

        async def research_event_stream() -> AsyncIterator[str]:
            yield f"data: {json.dumps(_research_event_payload(output))}\n\n"
            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(research_event_stream(), media_type="text/event-stream")

    history = await kernel.conversation_memory.get_history(payload.conversation_id)
    prompt = _build_prompt(history, payload.message, case_id=payload.case_id)
    await kernel.conversation_memory.add_message(payload.conversation_id, "user", payload.message)

    async def event_stream() -> AsyncIterator[str]:
        async for chunk in kernel.complete_stream(
            prompt,
            provider=payload.provider,
            conversation_id=payload.conversation_id,
        ):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
