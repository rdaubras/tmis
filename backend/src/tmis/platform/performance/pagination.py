from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

_MAX_PAGE_SIZE = 200


@dataclass(frozen=True, slots=True)
class PageRequest:
    """A pagination request (see docs/50-guide-performance.md —
    Pagination). `page` is 1-indexed; `page_size` is clamped to
    `_MAX_PAGE_SIZE` so a caller cannot force an unbounded query."""

    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be >= 1")
        if self.page_size < 1:
            raise ValueError("page_size must be >= 1")
        if self.page_size > _MAX_PAGE_SIZE:
            object.__setattr__(self, "page_size", _MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass(frozen=True, slots=True)
class Page(Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def has_next(self) -> bool:
        return self.page * self.page_size < self.total

    @property
    def has_previous(self) -> bool:
        return self.page > 1


def paginate(items: Sequence[T], request: PageRequest) -> Page[T]:
    """Slices an already-fetched, already-ordered sequence — the
    reference implementation for any in-memory store in TMIS. A store
    backed by a real database should push `LIMIT`/`OFFSET` down to SQL
    instead of calling this on a fully materialized list, but the
    `Page`/`PageRequest` shapes stay the same either way."""
    start = request.offset
    end = start + request.page_size
    return Page(
        items=list(items[start:end]),
        total=len(items),
        page=request.page,
        page_size=request.page_size,
    )
