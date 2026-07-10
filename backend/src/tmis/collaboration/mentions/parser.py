import re

from tmis.collaboration.mentions.schemas import MentionType

_MENTION_RE = re.compile(r"@(user|team|firm):([\w\-]+)")


class MentionParser:
    """Extracts `@user:<id>`, `@team:<id>` and `@firm:<id>` references
    from comment text (see docs/33-legal-collaboration.md — Mentions).
    A dependency-free regex parser — deliberately simple, since mention
    syntax is a display/authoring convention, not a place to over-engineer.
    """

    def extract(self, text: str) -> list[tuple[MentionType, str]]:
        return [(MentionType(kind), target_id) for kind, target_id in _MENTION_RE.findall(text)]
