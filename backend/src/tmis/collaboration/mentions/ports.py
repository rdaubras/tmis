from typing import Protocol

from tmis.collaboration.comments.schemas import Comment
from tmis.collaboration.mentions.schemas import Mention


class MentionEnginePort(Protocol):
    """Port implemented by every interchangeable mention engine."""

    def process(self, comment: Comment) -> list[Mention]: ...

    def list_for_comment(self, comment_id: str) -> list[Mention]: ...
