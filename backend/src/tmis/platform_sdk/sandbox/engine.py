import asyncio
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import structlog

from tmis.ai_team.agents.ports import KernelPort
from tmis.platform.metrics.bootstrap import get_metrics_registry
from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.schemas import ExtensionPermission
from tmis.platform_sdk.plugin_loader.engine import (
    PluginImplementationMissingError,
    PluginLoader,
    PluginNotPublishedError,
)
from tmis.platform_sdk.sandbox.schemas import ResourceQuota, SandboxExecutionResult
from tmis.platform_sdk.sdk.ports import EventPublisherPort
from tmis.platform_sdk.sdk.schemas import PluginContext

_logger = structlog.get_logger(__name__)


class SandboxExecutor:
    """The sprint's "SANDBOX" spec: limitation des permissions, accès
    contrôlé aux API, quotas de ressources, journalisation. This is a
    **logical** sandbox — permission gating, a sliding-window call
    quota, and a hard execution timeout around every plugin
    invocation — not OS-level process isolation. TMIS never `eval`s
    or `exec`s plugin source; every plugin is an ordinary, already-
    imported Python object (see `tmis.platform_sdk.plugin_loader`),
    so real code-level containment is a deployment concern (a
    plugin-per-pod story on top of `tmis.platform.deployment`,
    Sprint 10), out of scope for an in-process executor. See
    docs/65-architecture-platform-sdk.md."""

    def __init__(
        self,
        loader: PluginLoader,
        permissions: PermissionEngine,
        events: EventPublisherPort,
        kernel: KernelPort | None = None,
        quota: ResourceQuota = ResourceQuota(),
    ) -> None:
        self._loader = loader
        self._permissions = permissions
        self._events = events
        self._kernel = kernel
        self._quota = quota
        self._call_timestamps: dict[tuple[str, str], list[float]] = defaultdict(list)

    async def execute(
        self,
        firm_id: str,
        actor_id: str,
        plugin_id: str,
        payload: dict[str, Any],
        required_permission: ExtensionPermission | None = None,
    ) -> SandboxExecutionResult:
        """`required_permission` is `None` for a plugin that legitimately
        declares no permissions at all (see the "Workflow Validation"
        example plugin) — forcing every call site to name some
        permission would make such a plugin impossible to execute."""
        if required_permission is not None and not self._permissions.check(
            firm_id, plugin_id, required_permission
        ):
            return self._finish(plugin_id, success=False, error="permission refusée", started=None)

        if self._quota_exceeded(firm_id, plugin_id):
            return self._finish(
                plugin_id, success=False, error="quota d'appels dépassé", started=None
            )

        started = time.perf_counter()
        try:
            plugin = self._loader.load(plugin_id)
        except (
            KeyError,
            PluginNotPublishedError,
            PluginImplementationMissingError,
        ) as exc:
            return self._finish(plugin_id, success=False, error=str(exc), started=started)

        context = PluginContext(
            firm_id=firm_id,
            actor_id=actor_id,
            plugin_id=plugin_id,
            events=self._events,
            permissions=self._permissions.checker_for(firm_id, plugin_id),
            kernel=self._kernel,
        )
        self._record_call(firm_id, plugin_id)
        try:
            result = await asyncio.wait_for(
                plugin.invoke(context, payload), timeout=self._quota.max_execution_seconds
            )
        except TimeoutError:
            return self._finish(plugin_id, success=False, error="délai dépassé", started=started)
        except Exception as exc:  # noqa: BLE001 — a failing plugin must never crash the caller
            return self._finish(plugin_id, success=False, error=str(exc), started=started)

        return self._finish(plugin_id, success=True, result=result, started=started)

    def _quota_exceeded(self, firm_id: str, plugin_id: str) -> bool:
        timestamps = self._call_timestamps[(firm_id, plugin_id)]
        cutoff = time.monotonic() - 60
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)
        return len(timestamps) >= self._quota.max_calls_per_minute

    def _record_call(self, firm_id: str, plugin_id: str) -> None:
        self._call_timestamps[(firm_id, plugin_id)].append(time.monotonic())

    def _finish(
        self,
        plugin_id: str,
        *,
        success: bool,
        started: float | None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> SandboxExecutionResult:
        duration = time.perf_counter() - started if started is not None else 0.0
        status = "success" if success else "failed"
        _logger.info(
            "platform_sdk.sandbox_execution",
            plugin_id=plugin_id,
            status=status,
            duration_seconds=duration,
            error=error,
            occurred_at=datetime.now(UTC).isoformat(),
        )
        get_metrics_registry().counter(
            "platform_sdk_sandbox_executions_total", "Total sandboxed plugin executions"
        ).inc(plugin_id=plugin_id, status=status)
        get_metrics_registry().histogram(
            "platform_sdk_sandbox_duration_seconds", "Sandboxed plugin execution duration"
        ).observe(duration, plugin_id=plugin_id)
        return SandboxExecutionResult(
            plugin_id=plugin_id,
            success=success,
            result=result,
            error=error,
            duration_seconds=duration,
        )
