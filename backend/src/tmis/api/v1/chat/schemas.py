import uuid

from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    conversation_id: uuid.UUID
    message: str
    case_id: str | None = None
    provider: str | None = None
