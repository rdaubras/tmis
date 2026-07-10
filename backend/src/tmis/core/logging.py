import logging
import sys

import structlog

from tmis.platform.logging.redaction import RedactSensitiveFields


def configure_logging(debug: bool = False) -> None:
    """Configure structured JSON logging (stdout), per the Twelve Factor
    App model. Every log passes through `RedactSensitiveFields` (see
    docs/49-guide-supervision.md) before being rendered, so a stray
    `password=`/`token=`/`api_key=` kwarg anywhere in the codebase can
    never leak a credential into centralized logs."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if debug else logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            RedactSensitiveFields(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if debug else logging.INFO
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.typing.FilteringBoundLogger:
    logger: structlog.typing.FilteringBoundLogger = structlog.get_logger(name)
    return logger
