from typing import Protocol

from tmis.integration_hub.authentication.schemas import AuthCredentials, AuthMethod, AuthResult


class AuthStrategyPort(Protocol):
    """One pluggable authentication mechanism. `AuthenticationEngine`
    is closed over this narrow contract so a new method can be
    registered without touching the engine — same extensibility
    pattern as `workflow_automation.trigger_engine.TriggerMatcherPort`."""

    method: AuthMethod

    def authenticate(self, credentials: AuthCredentials) -> AuthResult: ...
