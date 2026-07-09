import pytest

pytestmark = pytest.mark.skip(
    reason="End-to-end scenarios (Playwright) are introduced once the frontend "
    "and auth flows exist (see docs/09-roadmap-30-sprints.md, Sprint 2+)."
)


def test_placeholder() -> None:
    assert True
