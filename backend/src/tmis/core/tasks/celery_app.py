"""The repo's one Celery app (Sprint 26 — Module Document + Persistance).

No Celery app existed anywhere in the codebase before this sprint (see the
now-superseded comment on `tmis.platform.health.bootstrap._check_queue`,
which explicitly deferred this to "Sprint 'Module Document'" — this is
that sprint). Every async task in the repo registers on this one app,
reusing the existing `redis_url` setting as both broker and result
backend — never a second Celery configuration per domain.
"""

from celery import Celery

from tmis.core.config import get_settings


def make_celery_app() -> Celery:
    settings = get_settings()
    app = Celery("tmis", broker=settings.redis_url, backend=settings.redis_url)
    app.conf.task_default_queue = "tmis"
    return app


celery_app = make_celery_app()
