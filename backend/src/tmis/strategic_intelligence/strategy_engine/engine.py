"""Heuristic, deterministic engine building coexisting strategic options.

No raw model call happens here — exactly like
`tmis.legal_reasoning.strategy.HeuristicStrategyEngine` and
`tmis.legal_reasoning.hypotheses.HeuristicHypothesisEngine`, this engine
only combines already-produced case material (hypotheses, arguments,
evidence). The "toutes les interactions IA passent par l'AI Intelligence
Fabric" constraint is therefore satisfied vacuously: nothing here bypasses
it because nothing here calls a model directly.
"""

from __future__ import annotations

import uuid

from tmis.strategic_intelligence.strategy_engine.schemas import (
    DEFAULT_STRATEGY_TYPES,
    Strategy,
)


def new_strategy_id() -> str:
    return f"strategy-{uuid.uuid4().hex[:12]}"


class StrategyEngine:
    """Builds one `Strategy` per candidate strategy type, never ranked."""

    def generate(
        self,
        *,
        case_id: str,
        question: str,
        hypotheses: tuple[str, ...] = (),
        main_arguments: tuple[str, ...] = (),
        counter_arguments: tuple[str, ...] = (),
        available_evidence: tuple[str, ...] = (),
        missing_evidence: tuple[str, ...] = (),
        candidate_types: tuple[str, ...] | None = None,
    ) -> list[Strategy]:
        types = candidate_types or DEFAULT_STRATEGY_TYPES
        strategies: list[Strategy] = []
        for strategy_type in types:
            strategies.append(
                self._build_one(
                    case_id=case_id,
                    question=question,
                    strategy_type=strategy_type,
                    hypotheses=hypotheses,
                    main_arguments=main_arguments,
                    counter_arguments=counter_arguments,
                    available_evidence=available_evidence,
                    missing_evidence=missing_evidence,
                )
            )
        return strategies

    def _build_one(
        self,
        *,
        case_id: str,
        question: str,
        strategy_type: str,
        hypotheses: tuple[str, ...],
        main_arguments: tuple[str, ...],
        counter_arguments: tuple[str, ...],
        available_evidence: tuple[str, ...],
        missing_evidence: tuple[str, ...],
        risks: tuple[str, ...] = (),
        recommended_steps: tuple[str, ...] = (),
        limitations: tuple[str, ...] = (),
    ) -> Strategy:
        confidence = self._estimate_confidence(
            available_evidence=available_evidence,
            missing_evidence=missing_evidence,
            counter_arguments=counter_arguments,
        )
        all_limitations = (
            *limitations,
            "Cette stratégie est une proposition ; elle ne constitue pas "
            "une décision juridique définitive et doit être validée par "
            "un professionnel du droit.",
        )
        return Strategy(
            id=new_strategy_id(),
            case_id=case_id,
            strategy_type=strategy_type,
            objective=f"{strategy_type} — en réponse à : {question}",
            hypotheses=hypotheses,
            main_arguments=main_arguments,
            counter_arguments=counter_arguments,
            available_evidence=available_evidence,
            missing_evidence=missing_evidence,
            recommended_steps=recommended_steps,
            risks=risks,
            confidence=confidence,
            limitations=all_limitations,
        )

    @staticmethod
    def _estimate_confidence(
        *,
        available_evidence: tuple[str, ...],
        missing_evidence: tuple[str, ...],
        counter_arguments: tuple[str, ...],
    ) -> float:
        total_evidence = len(available_evidence) + len(missing_evidence)
        if total_evidence == 0:
            coverage = 0.5
        else:
            coverage = len(available_evidence) / total_evidence
        penalty = min(0.3, 0.05 * len(counter_arguments))
        return round(max(0.0, min(1.0, coverage - penalty)), 2)
