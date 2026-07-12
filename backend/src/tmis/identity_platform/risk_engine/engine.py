from tmis.identity_platform.device_trust.engine import DeviceTrustEngine
from tmis.identity_platform.risk_engine.schemas import RiskAssessment, RiskLevel
from tmis.platform.rate_limiting.brute_force import BruteForceProtector
from tmis.platform.rate_limiting.schemas import LockoutStatus


def _identity_key(firm_id: str, user_id: str) -> str:
    return f"{firm_id}:{user_id}"


class RiskEngine:
    """Composes `device_trust.DeviceTrustEngine` and
    `platform.rate_limiting.brute_force.BruteForceProtector` (Sprint
    10) directly rather than reimplementing lockout/attempt counting
    — "détecter : connexions inhabituelles, appareils inconnus,
    tentatives répétées, comportements anormaux" (sprint requirement).
    A `MEDIUM`/`HIGH` assessment requires step-up MFA."""

    def __init__(
        self, device_trust_engine: DeviceTrustEngine, brute_force: BruteForceProtector
    ) -> None:
        self._devices = device_trust_engine
        self._brute_force = brute_force

    def assess_login(self, firm_id: str, user_id: str, device_id: str | None) -> RiskAssessment:
        reasons: list[str] = []
        status = self._brute_force.status(_identity_key(firm_id, user_id))
        if status.locked:
            reasons.append("verrouillage actif suite à des tentatives répétées")
        if device_id is None or not self._devices.is_trusted(firm_id, device_id):
            reasons.append("appareil inconnu ou non approuvé")

        if not reasons:
            return RiskAssessment(level=RiskLevel.LOW)
        level = RiskLevel.HIGH if status.locked else RiskLevel.MEDIUM
        return RiskAssessment(
            level=level, reasons=tuple(reasons), requires_step_up_mfa=level is not RiskLevel.LOW
        )

    def record_failure(self, firm_id: str, user_id: str) -> LockoutStatus:
        return self._brute_force.record_failure(_identity_key(firm_id, user_id))

    def record_success(self, firm_id: str, user_id: str) -> None:
        self._brute_force.record_success(_identity_key(firm_id, user_id))
