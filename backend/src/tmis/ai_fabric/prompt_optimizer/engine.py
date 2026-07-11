from tmis.ai.prompts.models import PromptTemplate
from tmis.ai.prompts.registry import PromptRegistry
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor
from tmis.ai_fabric.prompt_optimizer.schemas import OptimizedPrompt
from tmis.ai_fabric.token_manager.engine import estimate_tokens

_RESERVED_COMPLETION_TOKENS = 512


class PromptOptimizer:
    """The sprint's "PROMPT OPTIMIZER" module: adapts a prompt to the
    target model and manages variants. Storage and versioning are
    delegated entirely to `tmis.ai.prompts.PromptRegistry` (Sprint 2)
    per the sprint's own instruction that "les prompts restent
    versionnés dans le Prompt Registry" — this module only adds
    per-model adaptation (context-window-aware truncation) on top of
    a rendered prompt."""

    def __init__(self, registry: PromptRegistry) -> None:
        self._registry = registry

    def register(
        self, prompt_id: str, *, category: str, template: str, variables: tuple[str, ...] = ()
    ) -> PromptTemplate:
        return self._registry.register(
            prompt_id, category=category, template=template, variables=variables
        )

    def render(self, prompt_id: str, *, version: int | None = None, **kwargs: str) -> str:
        return self._registry.render(prompt_id, version=version, **kwargs)

    def adapt_for_model(self, prompt_text: str, model: ModelDescriptor) -> OptimizedPrompt:
        budget = max(1, model.max_context_tokens - _RESERVED_COMPLETION_TOKENS)
        words = prompt_text.split()
        if len(words) <= budget:
            return OptimizedPrompt(
                text=prompt_text, truncated=False, estimated_tokens=estimate_tokens(prompt_text)
            )
        truncated_text = " ".join(words[:budget])
        return OptimizedPrompt(
            text=truncated_text, truncated=True, estimated_tokens=estimate_tokens(truncated_text)
        )

    def history(self, prompt_id: str) -> list[PromptTemplate]:
        return self._registry.history(prompt_id)
