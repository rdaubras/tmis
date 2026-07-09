from tmis.ai.guardrails.exceptions import GuardrailViolation


class NonEmptyInputGuardrail:
    name = "non_empty_input"

    def validate(self, text: str) -> None:
        if not text or not text.strip():
            raise GuardrailViolation(self.name, "input must not be empty")


class MaxLengthInputGuardrail:
    def __init__(self, max_length: int = 32_000) -> None:
        self.name = "max_length_input"
        self._max_length = max_length

    def validate(self, text: str) -> None:
        if len(text) > self._max_length:
            raise GuardrailViolation(
                self.name, f"input exceeds {self._max_length} characters ({len(text)})"
            )
