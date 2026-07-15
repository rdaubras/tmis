import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

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


@router.post("/stream")
async def stream_chat(
    payload: ChatMessageRequest,
    kernel: TMISKernel = Depends(get_kernel),
    workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow),
) -> StreamingResponse:
    """Server-Sent Events endpoint for the general-purpose chat (Sprint 32
    scope: `TMISKernel.complete_stream()` only — no `ResearchOrchestrator`/
    LRE, that is Sprint 33, see docs/160-architecture-chat-ia.md).

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
