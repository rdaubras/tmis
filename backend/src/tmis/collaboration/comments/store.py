from tmis.collaboration.comments.schemas import Comment, CommentTargetType


class InMemoryCommentStore:
    """Implements `CommentStorePort` with an in-memory dict."""

    def __init__(self) -> None:
        self._comments: dict[str, Comment] = {}

    def get(self, comment_id: str) -> Comment | None:
        return self._comments.get(comment_id)

    def save(self, comment: Comment) -> None:
        self._comments[comment.id] = comment

    def list_for_target(self, target_type: CommentTargetType, target_id: str) -> list[Comment]:
        return [
            c
            for c in self._comments.values()
            if c.target_type == target_type and c.target_id == target_id
        ]

    def list_replies(self, parent_id: str) -> list[Comment]:
        return [c for c in self._comments.values() if c.parent_id == parent_id]

    def list_for_workspace(self, workspace_id: str) -> list[Comment]:
        return [c for c in self._comments.values() if c.workspace_id == workspace_id]
