from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class TenantContext:
    """The tenant an authenticated caller is scoped to for the
    duration of a request (see docs/47-guide-securite-entreprise.md —
    Multi-tenant hardening). Every read/write in TMIS that crosses a
    `firm_id` boundary should go through a check built on this."""

    firm_id: str
    actor_id: str


class TenantAccessError(PermissionError):
    """Raised when a caller scoped to one firm attempts to touch
    another firm's data — a systematic access-control failure, never
    silently ignored or downgraded to an empty result."""


def require_same_firm(context: TenantContext, resource_firm_id: str) -> None:
    """The single check every cross-tenant access point should call:
    fails loudly (`TenantAccessError`) rather than returning `None`/an
    empty list, so a missing check elsewhere cannot be mistaken for
    "no data found"."""
    if context.firm_id != resource_firm_id:
        raise TenantAccessError(
            f"Actor {context.actor_id!r} in firm {context.firm_id!r} "
            f"attempted to access a resource of firm {resource_firm_id!r}"
        )


def assert_tenant_isolated(
    records: Iterable[T], firm_id_of: Callable[[T], str], expected_firm_id: str
) -> None:
    """Test helper (see docs/47-guide-securite-entreprise.md — "tests
    d'étanchéité"): fails with every offending record's id-adjacent
    firm id if any record in `records` does not belong to
    `expected_firm_id`. Meant to be called from integration tests
    against every `list_for_firm`-style query across `cabinet_os` and
    `collaboration`, to catch a leaking store before it reaches an
    API response.
    """
    leaked = [firm_id_of(r) for r in records if firm_id_of(r) != expected_firm_id]
    if leaked:
        raise AssertionError(
            f"Tenant isolation breach: expected only firm {expected_firm_id!r}, "
            f"found records belonging to {sorted(set(leaked))!r}"
        )
