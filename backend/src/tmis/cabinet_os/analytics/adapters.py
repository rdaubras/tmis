from tmis.ai.kernel.kernel import TMISKernel


class NullAIUsageAdapter:
    """Implements `AIUsagePort`: always reports zero usage — the
    default when no `TMISKernel` is wired in (e.g. in isolated unit
    tests)."""

    def total_requests(self, firm_id: str) -> int:
        return 0


class KernelAIUsageAdapter:
    """Implements `AIUsagePort` on top of `TMISKernel.evaluator` — the
    one and only way `cabinet_os.analytics` touches AI, exactly as the
    sprint constraint requires ("les fonctionnalités IA doivent être
    consommées via le TMIS AI Kernel").

    **Known limitation** (see docs/39-cabinet-os.md — Portée du
    Sprint 9): the Kernel does not yet attribute a call to a firm, so
    `total_requests` returns the Kernel-wide count regardless of
    `firm_id` until the Kernel becomes multi-tenant-aware."""

    def __init__(self, kernel: TMISKernel) -> None:
        self._kernel = kernel

    def total_requests(self, firm_id: str) -> int:
        return len(self._kernel.evaluator.in_memory_metrics)
