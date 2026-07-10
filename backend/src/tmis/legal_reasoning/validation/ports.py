from typing import Protocol

from tmis.legal_reasoning.hypotheses.schemas import Hypothesis


class HypothesisValidationPort(Protocol):
    """Port implemented by every interchangeable hypothesis validation
    service. Validating or rejecting a hypothesis only ever mutates its
    `status` in place — every other hypothesis in the session is left
    untouched, so they keep coexisting (see
    docs/25-legal-reasoning.md — Hypothesis Engine)."""

    def validate(self, hypotheses: list[Hypothesis], hypothesis_id: str) -> Hypothesis: ...

    def reject(self, hypotheses: list[Hypothesis], hypothesis_id: str) -> Hypothesis: ...
