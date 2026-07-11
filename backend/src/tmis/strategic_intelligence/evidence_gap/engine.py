from tmis.strategic_intelligence.evidence_gap.schemas import EvidenceGap

_IMPACT_BY_RANK = ("élevé", "élevé", "moyen", "moyen", "faible")


class EvidenceGapEngine:
    """Turns a strategy's `missing_evidence` list into structured,
    always-explained gaps. Priority order in the input list is treated
    as the evaluator's own ranking — the earlier an item appears, the
    higher its estimated impact."""

    def identify(
        self,
        strategy_id: str,
        missing_evidence: tuple[str, ...],
        *,
        context: str = "",
    ) -> list[EvidenceGap]:
        gaps: list[EvidenceGap] = []
        for rank, item in enumerate(missing_evidence):
            impact = _IMPACT_BY_RANK[min(rank, len(_IMPACT_BY_RANK) - 1)]
            interest = (
                f"Cet élément permettrait de corroborer ou d'infirmer un point "
                f"clé de la stratégie {strategy_id}"
            )
            if context:
                interest += f" dans le contexte : {context}"
            gaps.append(
                EvidenceGap(
                    missing_evidence=item,
                    interest=interest + ".",
                    potential_impact=(
                        f"Impact potentiel estimé : {impact} sur la solidité "
                        "de la stratégie."
                    ),
                )
            )
        return gaps
