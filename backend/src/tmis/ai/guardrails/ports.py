from typing import Protocol

from tmis.ai.schemas.agent import AgentOutput


class InputGuardrailPort(Protocol):
    """Raises `GuardrailViolation` when `text` must not be sent to a model."""

    name: str

    def validate(self, text: str) -> None: ...


class OutputGuardrailPort(Protocol):
    """Returns non-fatal warnings about an `AgentOutput` (see
    `tmis.ai.guardrails.exceptions.GuardrailViolation` for why output
    guardrails never raise)."""

    name: str

    def validate(self, output: AgentOutput) -> list[str]: ...
