import uuid
from datetime import UTC, datetime

from tmis.collaboration.comments.ports import CommentStorePort
from tmis.collaboration.comments.schemas import Comment, CommentTargetType
from tmis.collaboration.comments.store import InMemoryCommentStore


class CommentService:
    """Adds comments and replies, and reconstructs threads (see
    docs/33-legal-collaboration.md — Comment Engine)."""

    def __init__(self, store: CommentStorePort | None = None) -> None:
        self._store: CommentStorePort = store or InMemoryCommentStore()

    def add(
        self,
        workspace_id: str,
        target_type: CommentTargetType,
        target_id: str,
        author_id: str,
        text: str,
        *,
        attachment_ids: tuple[str, ...] = (),
    ) -> Comment:
        comment = Comment(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            target_type=target_type,
            target_id=target_id,
            author_id=author_id,
            text=text,
            attachment_ids=attachment_ids,
            created_at=datetime.now(UTC),
        )
        self._store.save(comment)
        return comment

    def reply(self, parent_id: str, author_id: str, text: str) -> Comment:
        parent = self._store.get(parent_id)
        if parent is None:
            raise ValueError(f"Unknown comment {parent_id!r}")
        reply = Comment(
            id=str(uuid.uuid4()),
            workspace_id=parent.workspace_id,
            target_type=parent.target_type,
            target_id=parent.target_id,
            author_id=author_id,
            text=text,
            parent_id=parent_id,
            created_at=datetime.now(UTC),
        )
        self._store.save(reply)
        return reply

    def thread(self, comment_id: str) -> list[Comment]:
        return self._store.list_replies(comment_id)

    def list_for_target(self, target_type: CommentTargetType, target_id: str) -> list[Comment]:
        return self._store.list_for_target(target_type, target_id)
