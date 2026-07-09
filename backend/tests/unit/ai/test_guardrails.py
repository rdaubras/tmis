import pytest

from tmis.ai.guardrails.exceptions import GuardrailViolation
from tmis.ai.guardrails.input_guardrails import MaxLengthInputGuardrail, NonEmptyInputGuardrail
from tmis.ai.guardrails.output_guardrails import (
    CitationsTraceableGuardrail,
    NonEmptyResultGuardrail,
)
from tmis.ai.guardrails.pipeline import GuardrailPipeline
from tmis.ai.schemas.agent import AgentOutput
from tmis.ai.schemas.citation import Citation


def test_non_empty_input_guardrail_rejects_blank_text() -> None:
    guardrail = NonEmptyInputGuardrail()
    with pytest.raises(GuardrailViolation):
        guardrail.validate("   ")


def test_non_empty_input_guardrail_accepts_text() -> None:
    NonEmptyInputGuardrail().validate("Bonjour")


def test_max_length_input_guardrail_rejects_too_long_text() -> None:
    guardrail = MaxLengthInputGuardrail(max_length=10)
    with pytest.raises(GuardrailViolation):
        guardrail.validate("x" * 11)


def test_citations_traceable_guardrail_flags_missing_reference() -> None:
    guardrail = CitationsTraceableGuardrail()
    output = AgentOutput(
        result={"ok": True},
        citations=[Citation(source_id="1", connector="codes", excerpt="", reference="")],
    )
    warnings = guardrail.validate(output)
    assert len(warnings) == 1


def test_non_empty_result_guardrail_flags_empty_result() -> None:
    guardrail = NonEmptyResultGuardrail()
    assert guardrail.validate(AgentOutput(result={})) != []
    assert guardrail.validate(AgentOutput(result={"a": 1})) == []


def test_pipeline_validate_input_raises_on_first_violation() -> None:
    pipeline = GuardrailPipeline()
    with pytest.raises(GuardrailViolation):
        pipeline.validate_input("")


def test_pipeline_validate_output_aggregates_all_warnings() -> None:
    pipeline = GuardrailPipeline()
    output = AgentOutput(
        result={},
        citations=[Citation(source_id="1", connector="codes", excerpt="", reference="")],
    )
    warnings = pipeline.validate_output(output)
    assert len(warnings) == 2  # empty result + untraceable citation
