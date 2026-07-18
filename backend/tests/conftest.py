"""Shared fixtures usable from anywhere under `tests/`."""

import socket
import threading
from collections.abc import Iterator

import pytest


@pytest.fixture
def redis_ping_server() -> Iterator[str]:
    """A real TCP server, on an ephemeral port, that answers every
    request with a RESP `+PONG` reply — enough for `redis.Redis.ping()`
    to succeed against a genuine socket round-trip, without depending on
    a `redis-server` binary/service being available in every environment
    this suite runs in (deliberately: several tests, e.g.
    `tests/integration/ai/test_sprint28_backend_fallback.py`, rely on
    the *default* `TMIS_REDIS_URL` staying unreachable in CI, so this
    suite must never make a real Redis broadly reachable)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    sock.settimeout(0.2)
    stop = threading.Event()

    def _serve() -> None:
        while not stop.is_set():
            try:
                conn, _ = sock.accept()
            except TimeoutError:
                continue
            with conn:
                conn.settimeout(2)
                try:
                    while True:
                        data = conn.recv(4096)
                        if not data:
                            break
                        conn.sendall(b"+PONG\r\n")
                except OSError:
                    pass

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    port = sock.getsockname()[1]
    try:
        yield f"redis://127.0.0.1:{port}/0"
    finally:
        stop.set()
        thread.join(timeout=1)
        sock.close()
