from tmis.ai.prompts.models import PromptTemplate


class PromptRegistry:
    """In-memory prompt store, keyed by id, keeping every version (history).

    See docs/13-guides-extension.md for how a new prompt should be added.
    """

    def __init__(self) -> None:
        self._history: dict[str, list[PromptTemplate]] = {}

    def register(
        self, prompt_id: str, *, category: str, template: str, variables: tuple[str, ...] = ()
    ) -> PromptTemplate:
        existing = self._history.setdefault(prompt_id, [])
        next_version = existing[-1].version + 1 if existing else 1
        prompt = PromptTemplate(
            id=prompt_id,
            version=next_version,
            category=category,
            template=template,
            variables=variables,
        )
        existing.append(prompt)
        return prompt

    def get(self, prompt_id: str, *, version: int | None = None) -> PromptTemplate:
        versions = self._history.get(prompt_id)
        if not versions:
            raise KeyError(f"Unknown prompt: {prompt_id!r}")
        if version is None:
            return versions[-1]
        for prompt in versions:
            if prompt.version == version:
                return prompt
        raise KeyError(f"Unknown version {version} for prompt {prompt_id!r}")

    def render(self, prompt_id: str, *, version: int | None = None, **kwargs: str) -> str:
        return self.get(prompt_id, version=version).render(**kwargs)

    def history(self, prompt_id: str) -> list[PromptTemplate]:
        return list(self._history.get(prompt_id, []))
