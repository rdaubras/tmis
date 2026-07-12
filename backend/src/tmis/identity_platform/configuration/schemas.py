from dataclasses import dataclass, field

from tmis.identity_platform.authentication.schemas import AuthMethod


@dataclass(slots=True)
class IdentityConfiguration:
    """Per-firm identity & authentication configuration — which auth
    methods a firm allows, whether MFA is mandatory, how long a
    session may live, how a new device is treated by default. Every
    firm gets sane defaults at onboarding (`tenant_management.
    TenantManagementEngine.onboard_firm`) and may override them
    later; nothing here is hardcoded platform-wide."""

    firm_id: str
    allowed_auth_methods: frozenset[AuthMethod] = field(
        default_factory=lambda: frozenset(AuthMethod)
    )
    mfa_required: bool = False
    session_ttl_hours: int = 8
    new_devices_require_step_up_mfa: bool = True
