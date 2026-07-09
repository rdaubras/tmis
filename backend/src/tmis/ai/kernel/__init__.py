"""AI Kernel: the single entry point for every AI capability in TMIS.

`TMISKernel` initializes and wires providers, connectors, memory, cache,
events, prompts, tools, guardrails, evaluation and RAG. No other package
is allowed to talk to a model provider or a connector directly — see
docs/10-ai-kernel.md.
"""

from tmis.ai.kernel.config import KernelConfig, get_kernel_config
from tmis.ai.kernel.kernel import TMISKernel

__all__ = ["TMISKernel", "KernelConfig", "get_kernel_config"]
