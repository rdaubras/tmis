import uuid

import pytest

from tmis.ai.memory.case_memory import CaseMemory
from tmis.ai.memory.conversation_memory import ConversationMemory
from tmis.ai.memory.in_memory_store import InMemoryStore
from tmis.ai.memory.user_memory import UserMemory
from tmis.ai.memory.workflow_memory import WorkflowMemory


@pytest.mark.asyncio
async def test_conversation_memory_records_history_in_order() -> None:
    memory = ConversationMemory(InMemoryStore())
    conversation_id = uuid.uuid4()

    await memory.add_message(conversation_id, "user", "Bonjour")
    await memory.add_message(conversation_id, "assistant", "Bonjour, comment puis-je aider ?")

    assert await memory.get_history(conversation_id) == [
        "user: Bonjour",
        "assistant: Bonjour, comment puis-je aider ?",
    ]


@pytest.mark.asyncio
async def test_conversation_memory_clear_empties_history() -> None:
    memory = ConversationMemory(InMemoryStore())
    conversation_id = uuid.uuid4()
    await memory.add_message(conversation_id, "user", "Bonjour")

    await memory.clear(conversation_id)

    assert await memory.get_history(conversation_id) == []


@pytest.mark.asyncio
async def test_case_memory_notes_are_scoped_per_case() -> None:
    memory = CaseMemory(InMemoryStore())
    case_a, case_b = uuid.uuid4(), uuid.uuid4()

    await memory.add_note(case_a, "Fait important A")
    await memory.add_note(case_b, "Fait important B")

    assert await memory.get_notes(case_a) == ["Fait important A"]
    assert await memory.get_notes(case_b) == ["Fait important B"]


@pytest.mark.asyncio
async def test_workflow_memory_records_trace() -> None:
    memory = WorkflowMemory(InMemoryStore())
    workflow_id = uuid.uuid4()

    await memory.record_step(workflow_id, "analysis_step")
    await memory.record_step(workflow_id, "research_step")

    assert await memory.get_trace(workflow_id) == ["analysis_step", "research_step"]


@pytest.mark.asyncio
async def test_user_memory_records_activity() -> None:
    memory = UserMemory(InMemoryStore())
    user_id = uuid.uuid4()

    await memory.record_activity(user_id, "searched:responsabilité civile")

    assert await memory.get_recent_activity(user_id) == ["searched:responsabilité civile"]
