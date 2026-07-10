from typing import Protocol

from tmis.collaboration.comments.schemas import Comment, CommentTargetType


class CommentStorePort(Protocol):
    """Port implemented by every interchangeable comment store."""

    def get(self, comment_id: str) -> Comment | None: ...

    def save(self, comment: Comment) -> None: ...

    def list_for_target(
        self, target_type: CommentTargetType, target_id: str
    ) -> list[Comment]: ...

    def list_replies(self, parent_id: str) -> list[Comment]: ...

    def list_for_workspace(self, workspace_id: str) -> list[Comment]: ...


class CommentServicePort(Protocol):
    """Port implemented by every interchangeable comment service."""

    def add(
        self,
        workspace_id: str,
        target_type: CommentTargetType,
        target_id: str,
        author_id: str,
        text: str,
        *,
        attachment_ids: tuple[str, ...] = (),
    ) -> Comment: ...

    def reply(self, parent_id: str, author_id: str, text: str) -> Comment: ...

    def thread(self, comment_id: str) -> list[Comment]: ...

    def list_for_target(self, target_type: CommentTargetType, target_id: str) -> list[Comment]: ...
