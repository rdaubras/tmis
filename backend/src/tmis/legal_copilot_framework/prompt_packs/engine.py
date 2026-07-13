from tmis.ai.prompts.registry import PromptRegistry
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor
from tmis.ai_fabric.prompt_optimizer.engine import PromptOptimizer
from tmis.ai_fabric.prompt_optimizer.schemas import OptimizedPrompt
from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.legal_copilot_framework.prompt_packs.ports import PromptPackStorePort
from tmis.legal_copilot_framework.prompt_packs.schemas import PromptPack


class PromptPackEngine:
    """Adds inheritance and override resolution on top of `ai.prompts.
    PromptRegistry` (Sprint 2) and `ai_fabric.prompt_optimizer.
    PromptOptimizer` (Sprint 14) — neither stores or renders a prompt
    a second time; this engine only resolves *which* registered prompt
    id applies for a given pack before delegating."""

    def __init__(
        self,
        store: PromptPackStorePort,
        prompt_registry: PromptRegistry,
        prompt_optimizer: PromptOptimizer,
    ) -> None:
        self._store = store
        self._prompt_registry = prompt_registry
        self._prompt_optimizer = prompt_optimizer

    def register_pack(
        self,
        pack_id: str,
        name: str,
        domain: LegalDomain,
        *,
        system_prompt_ids: tuple[str, ...] = (),
        business_prompt_ids: tuple[str, ...] = (),
        parent_pack_id: str | None = None,
        overrides: dict[str, str] | None = None,
    ) -> PromptPack:
        existing = self._store.history(pack_id)
        version = existing[-1].version + 1 if existing else 1
        pack = PromptPack(
            id=pack_id,
            name=name,
            domain=domain,
            version=version,
            system_prompt_ids=system_prompt_ids,
            business_prompt_ids=business_prompt_ids,
            parent_pack_id=parent_pack_id,
            overrides=dict(overrides or {}),
        )
        self._store.save(pack)
        return pack

    def get(self, pack_id: str, version: int | None = None) -> PromptPack:
        pack = self._store.get(pack_id, version)
        if pack is None:
            raise KeyError(pack_id)
        return pack

    def history(self, pack_id: str) -> list[PromptPack]:
        return self._store.history(pack_id)

    def resolve_prompt_id(self, pack_id: str, prompt_id: str) -> str:
        """Walks the override/inheritance chain: this pack's own
        override wins, else the parent pack's, else the base
        `prompt_id` unchanged."""
        pack = self.get(pack_id)
        if prompt_id in pack.overrides:
            return pack.overrides[prompt_id]
        if pack.parent_pack_id is not None:
            return self.resolve_prompt_id(pack.parent_pack_id, prompt_id)
        return prompt_id

    def render(self, pack_id: str, prompt_id: str, **kwargs: str) -> str:
        effective_id = self.resolve_prompt_id(pack_id, prompt_id)
        return self._prompt_registry.get(effective_id).render(**kwargs)

    def render_for_model(
        self, pack_id: str, prompt_id: str, model: ModelDescriptor, **kwargs: str
    ) -> OptimizedPrompt:
        rendered = self.render(pack_id, prompt_id, **kwargs)
        return self._prompt_optimizer.adapt_for_model(rendered, model)
