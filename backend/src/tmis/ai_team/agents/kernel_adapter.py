from tmis.ai.kernel.kernel import TMISKernel


class KernelAgentAdapter:
    """Implements `KernelPort` on top of the real `TMISKernel` (see
    docs/53-guide-creation-agent.md). The only file in `ai_team` that
    imports `TMISKernel` directly — every agent depends on `KernelPort`
    instead, so swapping in a test double never requires touching an
    agent's own code."""

    def __init__(self, kernel: TMISKernel) -> None:
        self._kernel = kernel

    async def complete(self, prompt: str) -> str:
        response = await self._kernel.complete(prompt)
        return response.text
