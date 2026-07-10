from dataclasses import dataclass
from enum import Enum


class MentionType(str, Enum):
    USER = "user"
    TEAM = "team"
    FIRM = "firm"


@dataclass(frozen=True, slots=True)
class Mention:
    id: str
    comment_id: str
    mention_type: MentionType
    target_id: str
