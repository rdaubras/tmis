from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Critique:
    """A structured critique of one agent's production (see
    docs/57-guide-critique.md). Never a free-form paragraph: `issues`
    and `suggestions` are explicit lists so a reviewer (human or
    another engine) can act on each point independently."""

    target_sub_task_id: str
    target_agent_id: str
    issues: tuple[str, ...] = field(default_factory=tuple)
    suggestions: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_clean(self) -> bool:
        return not self.issues
