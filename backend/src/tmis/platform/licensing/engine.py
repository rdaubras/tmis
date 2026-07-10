import uuid
from datetime import UTC, datetime, timedelta

from tmis.cabinet_os.subscriptions.schemas import PlanTier
from tmis.platform.licensing.ports import LicenseStorePort
from tmis.platform.licensing.schemas import (
    License,
    LicenseValidationResult,
    default_seats_for_plan,
    features_for_plan,
)
from tmis.platform.licensing.signing import LicenseKeySigner

_FIELD_SEP = "|"


def _encode_payload(license_id: str, firm_id: str, plan: PlanTier, expires_at: datetime) -> str:
    return _FIELD_SEP.join([license_id, firm_id, plan.value, expires_at.isoformat()])


def _decode_payload(payload: str) -> tuple[str, str, PlanTier, datetime] | None:
    parts = payload.split(_FIELD_SEP)
    if len(parts) != 4:
        return None
    license_id, firm_id, plan_value, expires_at_raw = parts
    try:
        plan = PlanTier(plan_value)
        expires_at = datetime.fromisoformat(expires_at_raw)
    except ValueError:
        return None
    return license_id, firm_id, plan, expires_at


class LicenseEngine:
    """Implements `LicenseEnginePort` (see
    docs/47-guide-securite-entreprise.md — Licensing). License keys are
    HMAC-signed via `LicenseKeySigner` so a key handed to a firm cannot
    be forged or silently edited (e.g. to raise its own seat count or
    push out its expiry) without invalidating the signature."""

    def __init__(self, store: LicenseStorePort, signer: LicenseKeySigner) -> None:
        self._store = store
        self._signer = signer

    def issue(self, firm_id: str, plan: PlanTier, *, duration_days: int = 365) -> License:
        license_id = str(uuid.uuid4())
        issued_at = datetime.now(UTC)
        expires_at = issued_at + timedelta(days=duration_days)
        key = self._signer.sign(_encode_payload(license_id, firm_id, plan, expires_at))
        license_ = License(
            id=license_id,
            firm_id=firm_id,
            plan=plan,
            seats=default_seats_for_plan(plan),
            features=features_for_plan(plan),
            issued_at=issued_at,
            expires_at=expires_at,
            key=key,
        )
        self._store.save(license_)
        return license_

    def renew(self, firm_id: str, *, extension_days: int = 365) -> License:
        existing = self._store.get_for_firm(firm_id)
        if existing is None:
            raise ValueError(f"no license on file for firm {firm_id}")
        now = datetime.now(UTC)
        new_expiry = max(existing.expires_at, now) + timedelta(days=extension_days)
        key = self._signer.sign(_encode_payload(existing.id, firm_id, existing.plan, new_expiry))
        renewed = License(
            id=existing.id,
            firm_id=existing.firm_id,
            plan=existing.plan,
            seats=existing.seats,
            features=existing.features,
            issued_at=existing.issued_at,
            expires_at=new_expiry,
            key=key,
            renewed_at=now,
        )
        self._store.save(renewed)
        return renewed

    def validate(self, key: str) -> LicenseValidationResult:
        payload = self._signer.verify(key)
        if payload is None:
            return LicenseValidationResult(valid=False, reason="invalid or tampered license key")
        decoded = _decode_payload(payload)
        if decoded is None:
            return LicenseValidationResult(valid=False, reason="malformed license payload")
        license_id, firm_id, _plan, _expires_at = decoded
        stored = self._store.get(license_id)
        if stored is None or stored.firm_id != firm_id:
            return LicenseValidationResult(valid=False, reason="license not found")
        if stored.key != key:
            return LicenseValidationResult(valid=False, reason="license key has been superseded")
        if stored.is_expired():
            return LicenseValidationResult(valid=False, reason="license expired")
        return LicenseValidationResult(valid=True)

    def has_feature(self, firm_id: str, feature: str) -> bool:
        license_ = self._store.get_for_firm(firm_id)
        return license_ is not None and license_.has_feature(feature)

    def seats_remaining(self, firm_id: str, seats_in_use: int) -> int:
        license_ = self._store.get_for_firm(firm_id)
        if license_ is None:
            return 0
        return max(0, license_.seats - seats_in_use)
