from functools import lru_cache

from tmis.core.config import get_settings
from tmis.platform.licensing.engine import LicenseEngine
from tmis.platform.licensing.signing import LicenseKeySigner
from tmis.platform.licensing.store import InMemoryLicenseStore


@lru_cache
def get_license_key_signer() -> LicenseKeySigner:
    """Process-wide `LicenseKeySigner` singleton — shared by
    `get_license_engine` (firm-level signed license, Sprint 10) and
    `business_platform.licenses.LicenseEngine` (per-holder license
    grants, Sprint 20) so both sign with the same key material."""
    settings = get_settings()
    return LicenseKeySigner(settings.license_signing_key)


@lru_cache
def get_license_engine() -> LicenseEngine:
    """Process-wide `LicenseEngine` singleton — see
    docs/47-guide-securite-entreprise.md."""
    return LicenseEngine(InMemoryLicenseStore(), get_license_key_signer())
