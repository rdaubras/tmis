from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    reason: str = ""
    requires_second_validation: bool = False
