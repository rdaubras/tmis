from tmis.ai.guardrails.input_guardrails import MaxLengthInputGuardrail, NonEmptyInputGuardrail
from tmis.ai.guardrails.output_guardrails import (
    CitationsTraceableGuardrail,
    NonEmptyResultGuardrail,
)
from tmis.ai.guardrails.ports import InputGuardrailPort, OutputGuardrailPort
from tmis.ai.schemas.agent import AgentOutput


class GuardrailPipeline:
    """Runs every registered input/output guardrail.

    `validate_input` raises on the first violation (fail fast, before any
    model call happens); `validate_output` never raises — it collects
    warnings from every guardrail so the caller can decide what to do with
    them (see docs/07-strategie-securite.md).
    """

    def __init__(
        self,
        input_guardrails: list[InputGuardrailPort] | None = None,
        output_guardrails: list[OutputGuardrailPort] | None = None,
    ) -> None:
        self._input_guardrails = input_guardrails or [
            NonEmptyInputGuardrail(),
            MaxLengthInputGuardrail(),
        ]
        self._output_guardrails = output_guardrails or [
            CitationsTraceableGuardrail(),
            NonEmptyResultGuardrail(),
        ]

    def validate_input(self, text: str) -> None:
        for guardrail in self._input_guardrails:
            guardrail.validate(text)

    def validate_output(self, output: AgentOutput) -> list[str]:
        warnings: list[str] = []
        for guardrail in self._output_guardrails:
            warnings.extend(guardrail.validate(output))
        return warnings
