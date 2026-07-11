import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_review_id() -> str:
    return f"rev-{uuid.uuid4()}"


class InvalidRatingError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Review:
    id: str
    plugin_id: str
    firm_id: str
    rating: int
    comment: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not 1 <= self.rating <= 5:
            raise InvalidRatingError(f"rating must be in [1, 5], got {self.rating}")
