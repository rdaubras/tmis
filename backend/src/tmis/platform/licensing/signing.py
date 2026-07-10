import base64
import hashlib
import hmac


class LicenseKeySigner:
    """HMAC-SHA256 signer producing tamper-evident license keys of the
    form `<base64-payload>.<hex-signature>`. Not encryption — the
    payload is legible, only its integrity is protected. Anyone
    holding `secret` can forge keys, so it must be kept server-side
    only (see docs/47-guide-securite-entreprise.md — Licensing)."""

    def __init__(self, secret: str) -> None:
        self._secret = secret.encode()

    def _signature(self, payload_b64: str) -> str:
        return hmac.new(self._secret, payload_b64.encode(), hashlib.sha256).hexdigest()

    def sign(self, payload: str) -> str:
        payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode()
        return f"{payload_b64}.{self._signature(payload_b64)}"

    def verify(self, key: str) -> str | None:
        """Returns the decoded payload if `key`'s signature is valid,
        else `None`."""
        try:
            payload_b64, signature = key.split(".", 1)
        except ValueError:
            return None
        if not hmac.compare_digest(signature, self._signature(payload_b64)):
            return None
        try:
            return base64.urlsafe_b64decode(payload_b64.encode()).decode()
        except Exception:
            return None
