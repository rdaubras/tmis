from tmis.collaboration.comments.schemas import CommentTargetType
from tmis.collaboration.comments.service import CommentService
from tmis.collaboration.mentions.engine import MentionEngine
from tmis.collaboration.mentions.parser import MentionParser
from tmis.collaboration.mentions.schemas import MentionType
from tmis.collaboration.notifications.engine import NotificationEngine
from tmis.collaboration.notifications.schemas import NotificationChannel


def test_add_comment_attaches_to_a_target() -> None:
    service = CommentService()
    comment = service.add(
        "ws-1", CommentTargetType.CASE, "case-1", "author-1", "Premier commentaire"
    )

    assert comment.target_type is CommentTargetType.CASE
    assert comment.parent_id is None


def test_reply_forms_a_thread() -> None:
    service = CommentService()
    parent = service.add("ws-1", CommentTargetType.TASK, "task-1", "author-1", "Question ?")
    reply = service.reply(parent.id, "author-2", "Réponse.")

    thread = service.thread(parent.id)

    assert reply.parent_id == parent.id
    assert reply.target_type is parent.target_type
    assert reply.target_id == parent.target_id
    assert thread == [reply]


def test_list_for_target_returns_only_matching_comments() -> None:
    service = CommentService()
    service.add("ws-1", CommentTargetType.DOCUMENT, "doc-1", "author-1", "Sur ce document")
    service.add("ws-1", CommentTargetType.DOCUMENT, "doc-2", "author-1", "Sur un autre document")

    found = service.list_for_target(CommentTargetType.DOCUMENT, "doc-1")

    assert len(found) == 1
    assert found[0].target_id == "doc-1"


def test_mention_parser_extracts_all_three_kinds() -> None:
    parser = MentionParser()
    extracted = parser.extract("Voir @user:u1, @team:t1 et @firm:f1 pour validation.")

    assert extracted == [
        (MentionType.USER, "u1"),
        (MentionType.TEAM, "t1"),
        (MentionType.FIRM, "f1"),
    ]


def test_mention_parser_returns_empty_list_when_no_mentions() -> None:
    parser = MentionParser()
    assert parser.extract("Rien à signaler ici.") == []


def test_mention_engine_creates_mentions_and_notifies_user_mentions() -> None:
    notifications = NotificationEngine()
    engine = MentionEngine(notifications)
    comment_service = CommentService()
    comment = comment_service.add(
        "ws-1", CommentTargetType.CASE, "case-1", "author-1", "Pour avis @user:u1"
    )

    mentions = engine.process(comment)

    assert len(mentions) == 1
    assert mentions[0].mention_type is MentionType.USER
    assert mentions[0].target_id == "u1"

    inbox = notifications.list_for_recipient("u1")
    assert len(inbox) == 1
    assert inbox[0].channel is NotificationChannel.IN_APP
    assert inbox[0].type == "mention"


def test_mention_engine_does_not_notify_team_or_firm_without_a_resolver() -> None:
    """No team/firm membership roster exists yet (known limitation, see
    docs/33-legal-collaboration.md) — those mentions are still recorded,
    they simply resolve to zero recipients unless a resolver is
    injected."""
    notifications = NotificationEngine()
    engine = MentionEngine(notifications)
    comment_service = CommentService()
    comment = comment_service.add(
        "ws-1", CommentTargetType.CASE, "case-1", "author-1", "Pour avis @team:t1 @firm:f1"
    )

    mentions = engine.process(comment)

    assert {m.mention_type for m in mentions} == {MentionType.TEAM, MentionType.FIRM}
    assert notifications.list_for_recipient("t1") == []
    assert notifications.list_for_recipient("f1") == []


def test_mention_engine_custom_resolver_can_expand_team_mentions() -> None:
    notifications = NotificationEngine()

    def resolver(mention_type: MentionType, target_id: str) -> list[str]:
        if mention_type is MentionType.TEAM:
            return ["u1", "u2"]
        return [target_id] if mention_type is MentionType.USER else []

    engine = MentionEngine(notifications, recipient_resolver=resolver)
    comment_service = CommentService()
    comment = comment_service.add(
        "ws-1", CommentTargetType.CASE, "case-1", "author-1", "@team:litige"
    )

    engine.process(comment)

    assert len(notifications.list_for_recipient("u1")) == 1
    assert len(notifications.list_for_recipient("u2")) == 1


def test_mention_engine_list_for_comment_returns_recorded_mentions() -> None:
    notifications = NotificationEngine()
    engine = MentionEngine(notifications)
    comment_service = CommentService()
    comment = comment_service.add(
        "ws-1", CommentTargetType.CASE, "case-1", "author-1", "@user:u1"
    )

    engine.process(comment)

    assert len(engine.list_for_comment(comment.id)) == 1
    assert engine.list_for_comment("unknown-comment") == []
