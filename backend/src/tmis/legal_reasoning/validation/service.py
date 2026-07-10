from tmis.legal_reasoning.hypotheses.schemas import Hypothesis, HypothesisStatus


class HypothesisValidationService:
    """Implements `HypothesisValidationPort`: an avocat validates or
    rejects exactly one hypothesis at a time by mutating its `status`;
    every other hypothesis in the list — including ones that contradict
    the validated one — is left exactly as it was. TMIS never resolves
    that contradiction on the lawyer's behalf (see
    docs/25-legal-reasoning.md — Hypothesis Engine)."""

    def validate(self, hypotheses: list[Hypothesis], hypothesis_id: str) -> Hypothesis:
        return self._set_status(hypotheses, hypothesis_id, HypothesisStatus.VALIDATED)

    def reject(self, hypotheses: list[Hypothesis], hypothesis_id: str) -> Hypothesis:
        return self._set_status(hypotheses, hypothesis_id, HypothesisStatus.REJECTED)

    def _set_status(
        self, hypotheses: list[Hypothesis], hypothesis_id: str, status: HypothesisStatus
    ) -> Hypothesis:
        for hypothesis in hypotheses:
            if hypothesis.id == hypothesis_id:
                hypothesis.status = status
                return hypothesis
        raise ValueError(f"Unknown hypothesis: {hypothesis_id!r}")
