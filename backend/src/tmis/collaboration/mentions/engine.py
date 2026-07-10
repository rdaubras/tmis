import uuid
from collections.abc import Callable

from tmis.collaboration.comments.schemas import Comment
from tmis.collaboration.mentions.parser import MentionParser
from tmis.collaboration.mentions.schemas import Mention, MentionType
from tmis.collaboration.notifications.ports import NotificationEnginePort
from tmis.collaboration.notifications.schemas import NotificationChannel

RecipientResolver = Callable[[MentionType, str], list[str]]


def _default_resolver(mention_type: MentionType, target_id: str) -> list[str]:
    """USER mentions resolve to themselves; TEAM/FIRM mentions have no
    membership roster in this sprint (see docs/33-legal-collaboration.md
    — Mentions, known limitation), so they resolve to no recipients
    unless a real resolver is injected."""
    if mention_type is MentionType.USER:
        return [target_id]
    return []


class MentionEngine:
    """Implements `MentionEnginePort`: parses `@user:<id>` / `@team:<id>`
    / `@firm:<id>` references out of a comment's text and notifies the
    resolved recipients through the injected `NotificationEnginePort`
    (see docs/33-legal-collaboration.md — Mentions)."""

    def __init__(
        self,
        notification_engine: NotificationEnginePort,
        parser: MentionParser | None = None,
        recipient_resolver: RecipientResolver | None = None,
    ) -> None:
        self._notification_engine = notification_engine
        self._parser = parser if parser is not None else MentionParser()
        self._resolve = recipient_resolver if recipient_resolver is not None else _default_resolver
        self._mentions: dict[str, list[Mention]] = {}

    def process(self, comment: Comment) -> list[Mention]:
        extracted = self._parser.extract(comment.text)
        mentions: list[Mention] = []
        for mention_type, target_id in extracted:
            mention = Mention(
                id=str(uuid.uuid4()),
                comment_id=comment.id,
                mention_type=mention_type,
                target_id=target_id,
            )
            mentions.append(mention)
            for recipient_id in self._resolve(mention_type, target_id):
                self._notification_engine.dispatch(
                    workspace_id=comment.workspace_id,
                    recipient_id=recipient_id,
                    notification_type="mention",
                    payload={"comment_id": comment.id, "author_id": comment.author_id},
                    channels=[NotificationChannel.IN_APP],
                )
        self._mentions[comment.id] = mentions
        return mentions

    def list_for_comment(self, comment_id: str) -> list[Mention]:
        return list(self._mentions.get(comment_id, []))
