import asyncio
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from tmis.integration_hub.sandbox.schemas import ConnectorResourceQuota, SandboxExecutionResult


class ConnectorSandbox:
    """Logical sandbox around a connector call — a sliding-window call
    quota plus a hard execution timeout — "isoler l'exécution de
    chaque connecteur : quotas de ressources, timeout d'exécution,
    journalisation" (sprint requirement). Reimplemented locally rather
    than reusing `platform_sdk.sandbox.SandboxExecutor`, which is
    tightly coupled to Plugin System internals (`PluginLoader`,
    `PermissionEngine`, `PluginContext`, `KernelPort`) that have no
    equivalent here; only the quota+timeout *pattern* is mirrored."""

    def __init__(self, quota: ConnectorResourceQuota = ConnectorResourceQuota()) -> None:
        self._quota = quota
        self._call_timestamps: dict[tuple[str, str], list[float]] = defaultdict(list)

    def quota_exceeded(self, firm_id: str, connector_id: str) -> bool:
        timestamps = self._call_timestamps[(firm_id, connector_id)]
        cutoff = time.monotonic() - 60
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)
        return len(timestamps) >= self._quota.max_calls_per_minute

    def _record_call(self, firm_id: str, connector_id: str) -> None:
        self._call_timestamps[(firm_id, connector_id)].append(time.monotonic())

    async def run(
        self, firm_id: str, connector_id: str, operation: Callable[[], Awaitable[Any]]
    ) -> SandboxExecutionResult:
        if self.quota_exceeded(firm_id, connector_id):
            return SandboxExecutionResult(
                connector_id=connector_id, success=False, error="quota d'appels dépassé"
            )

        started = time.perf_counter()
        self._record_call(firm_id, connector_id)
        try:
            value = await asyncio.wait_for(operation(), timeout=self._quota.max_execution_seconds)
        except TimeoutError:
            return SandboxExecutionResult(
                connector_id=connector_id,
                success=False,
                error="délai dépassé",
                duration_seconds=time.perf_counter() - started,
            )
        except Exception as exc:  # noqa: BLE001 — a failing connector call must never crash the caller
            return SandboxExecutionResult(
                connector_id=connector_id,
                success=False,
                error=str(exc),
                duration_seconds=time.perf_counter() - started,
            )

        return SandboxExecutionResult(
            connector_id=connector_id,
            success=True,
            result=value,
            duration_seconds=time.perf_counter() - started,
        )
