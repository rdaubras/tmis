from functools import lru_cache

from tmis.ai.kernel.kernel import TMISKernel


@lru_cache
def get_kernel() -> TMISKernel:
    """Process-wide `TMISKernel` singleton.

    Shared by the API layer and every engine built on top of it (Document
    Intelligence, Case Intelligence) so they all publish/subscribe on the
    same `EventBus` — the seam that makes the "living case" automatic
    (see docs/10-ai-kernel.md and docs/19-case-intelligence.md).
    """
    return TMISKernel()
