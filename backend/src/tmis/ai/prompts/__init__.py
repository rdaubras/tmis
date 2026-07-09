"""Prompt Registry: prompts are never hardcoded inside an agent.

Every prompt is registered with an id, a version, a category and its
expected variables, and rendered through `PromptRegistry.render()`. This
is the seam that will carry future A/B testing and multi-language support
without touching any agent code (see docs/10-ai-kernel.md).
"""
