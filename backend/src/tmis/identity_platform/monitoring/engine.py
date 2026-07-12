from datetime import UTC, datetime, timedelta

from tmis.identity_platform.delegation.engine import DelegationEngine
from tmis.identity_platform.device_trust.engine import DeviceTrustEngine
from tmis.identity_platform.device_trust.schemas import DeviceTrustLevel
from tmis.identity_platform.mfa.engine import MfaEngine
from tmis.identity_platform.monitoring.schemas import IdentityDashboard
from tmis.identity_platform.policy_engine.engine import PolicyEngine
from tmis.identity_platform.security_events.bus import SecurityEventBus
from tmis.identity_platform.security_events.schemas import LoginFailed, MfaChallengeFailed
from tmis.identity_platform.session_manager.engine import SessionManager

_RISK_FLAVORED_EVENTS = (LoginFailed, MfaChallengeFailed)


class IdentityMonitoringEngine:
    """Composes the already-built engines to answer the sprint's
    dashboard requirement rather than duplicating their state.
    `security_events_total`/`high_risk_events_last_24h` read directly
    from `SecurityEventBus.history`, the append-only trail every
    other identity-platform module already publishes to."""

    def __init__(
        self,
        sessions: SessionManager,
        mfa: MfaEngine,
        devices: DeviceTrustEngine,
        delegations: DelegationEngine,
        policies: PolicyEngine,
        events: SecurityEventBus,
    ) -> None:
        self._sessions = sessions
        self._mfa = mfa
        self._devices = devices
        self._delegations = delegations
        self._policies = policies
        self._events = events

    def dashboard(self, firm_id: str) -> IdentityDashboard:
        now = datetime.now(UTC)
        cutoff = now - timedelta(hours=24)
        firm_events = [e for e in self._events.history if e.firm_id == firm_id]
        high_risk = [
            e
            for e in firm_events
            if isinstance(e, _RISK_FLAVORED_EVENTS) and e.occurred_at >= cutoff
        ]
        active_sessions = [s for s in self._sessions.list_for_firm(firm_id) if s.expires_at > now]
        trusted_devices = [
            d
            for d in self._devices.list_for_firm(firm_id)
            if d.trust_level is DeviceTrustLevel.TRUSTED
        ]

        return IdentityDashboard(
            firm_id=firm_id,
            active_sessions=len(active_sessions),
            mfa_enrolled_users=self._mfa.count_confirmed_for_firm(firm_id),
            trusted_devices=len(trusted_devices),
            active_delegations=len(self._delegations.active_delegations_for_firm(firm_id, now)),
            active_policies=len(self._policies.list_active_for_firm(firm_id)),
            security_events_total=len(firm_events),
            high_risk_events_last_24h=len(high_risk),
            computed_at=now,
        )
