import base64
import hashlib
import hmac
import secrets
import struct
import time

_DEFAULT_TIMESTEP = 30
_DEFAULT_DIGITS = 6
_DEFAULT_WINDOW = 1


def generate_secret() -> str:
    """A fresh base32 TOTP shared secret (RFC 6238) — no third-party
    dependency needed: TOTP is HMAC-SHA1 over a 30-second time
    counter, well within stdlib `hmac`/`hashlib`/`struct`/`base64`."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _hotp(secret: str, counter: int, digits: int) -> str:
    padding = "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(secret + padding)
    message = struct.pack(">Q", counter)
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % (10**digits)
    return str(code_int).zfill(digits)


def generate_totp(
    secret: str,
    *,
    timestep: int = _DEFAULT_TIMESTEP,
    digits: int = _DEFAULT_DIGITS,
    at: float | None = None,
) -> str:
    counter = int((at if at is not None else time.time()) // timestep)
    return _hotp(secret, counter, digits)


def verify_totp(
    secret: str,
    code: str,
    *,
    timestep: int = _DEFAULT_TIMESTEP,
    digits: int = _DEFAULT_DIGITS,
    window: int = _DEFAULT_WINDOW,
    at: float | None = None,
) -> bool:
    """Accepts a code from the current timestep or `window` steps
    either side, to tolerate clock drift between server and
    authenticator app — the standard TOTP verification practice."""
    now = at if at is not None else time.time()
    counter = int(now // timestep)
    return any(
        hmac.compare_digest(_hotp(secret, counter + offset, digits), code)
        for offset in range(-window, window + 1)
    )
