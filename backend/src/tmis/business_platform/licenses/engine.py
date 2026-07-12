from tmis.business_platform.licenses.ports import FloatingPoolStorePort, LicenseGrantStorePort
from tmis.business_platform.licenses.schemas import (
    FloatingLicensePool,
    LicenseGrant,
    LicenseType,
    default_expiry,
    expiry_in_hours,
    new_grant_id,
    now_utc,
)
from tmis.platform.licensing.signing import LicenseKeySigner

_FIELD_SEP = "|"


def _encode(grant_id: str, firm_id: str, license_type: LicenseType) -> str:
    return _FIELD_SEP.join([grant_id, firm_id, license_type.value])


class FloatingPoolExhaustedError(RuntimeError):
    pass


class LicenseEngine:
    """Assign/revoke/transfer license grants of the sprint's four
    types. Composes `platform.licensing.signing.LicenseKeySigner`
    directly (Sprint 10) for tamper-evident keys — never reimplements
    HMAC signing."""

    def __init__(
        self,
        grants: LicenseGrantStorePort,
        pools: FloatingPoolStorePort,
        signer: LicenseKeySigner,
    ) -> None:
        self._grants = grants
        self._pools = pools
        self._signer = signer

    def assign(
        self,
        firm_id: str,
        license_type: LicenseType,
        holder_id: str,
        *,
        duration_days: int = 365,
    ) -> LicenseGrant:
        if license_type is LicenseType.FLOATING:
            raise ValueError("use checkout_floating for FLOATING licenses")
        grant_id = new_grant_id()
        key = self._signer.sign(_encode(grant_id, firm_id, license_type))
        grant = LicenseGrant(
            id=grant_id,
            firm_id=firm_id,
            license_type=license_type,
            holder_id=holder_id,
            key=key,
            granted_at=now_utc(),
            expires_at=default_expiry(duration_days),
        )
        self._grants.save(grant)
        return grant

    def revoke(self, firm_id: str, grant_id: str) -> LicenseGrant:
        grant = self._require(firm_id, grant_id)
        grant.revoked = True
        self._grants.save(grant)
        return grant

    def transfer(self, firm_id: str, grant_id: str, new_holder_id: str) -> LicenseGrant:
        old = self._require(firm_id, grant_id)
        old.revoked = True
        self._grants.save(old)
        new_id = new_grant_id()
        key = self._signer.sign(_encode(new_id, firm_id, old.license_type))
        new_grant = LicenseGrant(
            id=new_id,
            firm_id=firm_id,
            license_type=old.license_type,
            holder_id=new_holder_id,
            key=key,
            granted_at=now_utc(),
            expires_at=old.expires_at,
            transferred_from=old.id,
        )
        self._grants.save(new_grant)
        return new_grant

    def set_floating_pool_capacity(self, firm_id: str, total_seats: int) -> FloatingLicensePool:
        pool = FloatingLicensePool(firm_id=firm_id, total_seats=total_seats)
        self._pools.save(pool)
        return pool

    def checkout_floating(
        self, firm_id: str, holder_id: str, *, duration_hours: int = 8
    ) -> LicenseGrant:
        pool = self._pools.get(firm_id)
        if pool is None:
            raise FloatingPoolExhaustedError(f"no floating pool configured for firm {firm_id!r}")
        checked_out = sum(
            1
            for g in self._grants.list_for_firm(firm_id)
            if g.license_type is LicenseType.FLOATING and g.is_active()
        )
        if checked_out >= pool.total_seats:
            raise FloatingPoolExhaustedError(f"floating pool exhausted for firm {firm_id!r}")
        grant_id = new_grant_id()
        key = self._signer.sign(_encode(grant_id, firm_id, LicenseType.FLOATING))
        grant = LicenseGrant(
            id=grant_id,
            firm_id=firm_id,
            license_type=LicenseType.FLOATING,
            holder_id=holder_id,
            key=key,
            granted_at=now_utc(),
            expires_at=expiry_in_hours(duration_hours),
        )
        self._grants.save(grant)
        return grant

    def checkin_floating(self, firm_id: str, grant_id: str) -> LicenseGrant:
        grant = self._require(firm_id, grant_id)
        grant.revoked = True
        self._grants.save(grant)
        return grant

    def active_grants_for_firm(self, firm_id: str) -> list[LicenseGrant]:
        return [g for g in self._grants.list_for_firm(firm_id) if g.is_active()]

    def active_grants_for_holder(self, firm_id: str, holder_id: str) -> list[LicenseGrant]:
        return [g for g in self._grants.list_for_holder(firm_id, holder_id) if g.is_active()]

    def validate(self, key: str) -> bool:
        return self._signer.verify(key) is not None

    def _require(self, firm_id: str, grant_id: str) -> LicenseGrant:
        grant = self._grants.get(firm_id, grant_id)
        if grant is None:
            raise KeyError(grant_id)
        return grant
