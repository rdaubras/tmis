import pytest

from tmis.legal_reasoning.hypotheses.schemas import Hypothesis, HypothesisStatus
from tmis.legal_reasoning.validation.service import HypothesisValidationService


def test_validate_sets_status_to_validated() -> None:
    hypothesis = Hypothesis(id="h1", description="d1")
    service = HypothesisValidationService()

    result = service.validate([hypothesis], "h1")

    assert result.status == HypothesisStatus.VALIDATED
    assert hypothesis.status == HypothesisStatus.VALIDATED


def test_reject_sets_status_to_rejected() -> None:
    hypothesis = Hypothesis(id="h1", description="d1")
    service = HypothesisValidationService()

    service.reject([hypothesis], "h1")

    assert hypothesis.status == HypothesisStatus.REJECTED


def test_validating_one_hypothesis_leaves_others_untouched() -> None:
    h1 = Hypothesis(id="h1", description="d1")
    h2 = Hypothesis(id="h2", description="d2")
    service = HypothesisValidationService()

    service.validate([h1, h2], "h1")

    assert h1.status == HypothesisStatus.VALIDATED
    assert h2.status == HypothesisStatus.PROPOSED


def test_validate_unknown_id_raises() -> None:
    service = HypothesisValidationService()
    with pytest.raises(ValueError, match="Unknown"):
        service.validate([], "does-not-exist")
