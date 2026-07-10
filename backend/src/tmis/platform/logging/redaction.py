from typing import Any

from structlog.typing import EventDict, WrappedLogger

_DEFAULT_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "hashed_password",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "secret",
        "client_secret",
        "api_key",
        "raw_key",
        "key_hash",
        "jwt_secret_key",
        "csrf_token",
    }
)
_REDACTED = "***REDACTED***"


class RedactSensitiveFields:
    """A structlog processor instance: masks any event-dict key (case-
    insensitively) that looks like a secret, so a stray
    `logger.info("login", password=raw_password)` never leaks a
    credential into centralized logs (see docs/49-guide-supervision.md
    — Logs structurés). Nested dicts and lists are redacted
    recursively. The sensitive-key set is configurable via the
    constructor, so a deployment can extend it without subclassing."""

    def __init__(self, sensitive_keys: frozenset[str] = _DEFAULT_SENSITIVE_KEYS) -> None:
        self._keys = sensitive_keys

    def __call__(self, logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
        return {k: self._redact_value(k, v) for k, v in event_dict.items()}

    def _redact_value(self, key: str, value: Any) -> Any:
        if key.lower() in self._keys:
            return _REDACTED
        if isinstance(value, dict):
            return {k: self._redact_value(k, v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._redact_value(key, item) for item in value]
        return value
