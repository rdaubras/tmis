import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("TMIS_DATABASE_URL"),
    reason="Integration tests require a running PostgreSQL instance (see docker-compose.yml).",
)


def test_placeholder_requires_database() -> None:
    """Real repository integration tests land with the `case` CRUD API (Sprint 4).

    See docs/09-roadmap-30-sprints.md.
    """
    assert True
