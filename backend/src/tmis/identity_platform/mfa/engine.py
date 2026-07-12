from tmis.identity_platform.mfa.ports import TotpEnrollmentStorePort
from tmis.identity_platform.mfa.schemas import TotpEnrollment
from tmis.identity_platform.mfa.totp import generate_secret, verify_totp


class MfaEngine:
    """TOTP enrollment and verification — "MFA (TOTP)" (sprint
    requirement). Enrollment stays unconfirmed until the user proves
    they can generate a valid code, so a mistyped or lost secret never
    silently locks an account into a broken MFA state."""

    def __init__(self, store: TotpEnrollmentStorePort) -> None:
        self._store = store

    def enroll(self, firm_id: str, user_id: str) -> TotpEnrollment:
        enrollment = TotpEnrollment(firm_id=firm_id, user_id=user_id, secret=generate_secret())
        self._store.save(enrollment)
        return enrollment

    def confirm(self, firm_id: str, user_id: str, code: str) -> bool:
        enrollment = self._store.get(firm_id, user_id)
        if enrollment is None or not verify_totp(enrollment.secret, code):
            return False
        enrollment.confirmed = True
        self._store.save(enrollment)
        return True

    def verify(self, firm_id: str, user_id: str, code: str) -> bool:
        enrollment = self._store.get(firm_id, user_id)
        if enrollment is None or not enrollment.confirmed:
            return False
        return verify_totp(enrollment.secret, code)

    def count_confirmed_for_firm(self, firm_id: str) -> int:
        return sum(1 for e in self._store.list_for_firm(firm_id) if e.confirmed)
