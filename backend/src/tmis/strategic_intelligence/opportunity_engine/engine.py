from tmis.strategic_intelligence.opportunity_engine.schemas import (
    OpportunityFinding,
    new_opportunity_id,
)


class OpportunityEngine:
    """Spots unexploited arguments, complementary documents worth
    fetching, clauses worth double-checking, and further research
    leads. Purely heuristic on already-produced strategy material —
    never a raw model call, so it never bypasses the AI Intelligence
    Fabric."""

    def find(
        self,
        strategy_id: str,
        *,
        main_arguments: tuple[str, ...] = (),
        unused_hypotheses: tuple[str, ...] = (),
        available_evidence: tuple[str, ...] = (),
        missing_evidence: tuple[str, ...] = (),
        clauses_to_verify: tuple[str, ...] = (),
    ) -> list[OpportunityFinding]:
        findings: list[OpportunityFinding] = []

        for hypothesis in unused_hypotheses:
            findings.append(
                OpportunityFinding(
                    id=new_opportunity_id(),
                    category="argument_inexploité",
                    description=hypothesis,
                    justification=(
                        f"L'hypothèse « {hypothesis} » n'est mobilisée par aucun "
                        "argument principal de cette stratégie : elle mérite "
                        "d'être évaluée comme argument complémentaire."
                    ),
                )
            )

        for evidence in missing_evidence:
            findings.append(
                OpportunityFinding(
                    id=new_opportunity_id(),
                    category="document_complémentaire",
                    description=evidence,
                    justification=(
                        f"L'élément « {evidence} » est actuellement manquant et "
                        "pourrait renforcer significativement le dossier s'il "
                        "est obtenu."
                    ),
                )
            )

        for clause in clauses_to_verify:
            findings.append(
                OpportunityFinding(
                    id=new_opportunity_id(),
                    category="clause_à_vérifier",
                    description=clause,
                    justification=(
                        f"La clause « {clause} » n'a pas été explicitement "
                        "analysée dans les arguments actuels et pourrait "
                        "modifier l'issue de la stratégie."
                    ),
                )
            )

        if len(main_arguments) < 2:
            findings.append(
                OpportunityFinding(
                    id=new_opportunity_id(),
                    category="recherche_additionnelle",
                    description=f"Approfondir la recherche juridique pour {strategy_id}",
                    justification=(
                        "Moins de deux arguments principaux sont actuellement "
                        "recensés : une recherche additionnelle est recommandée "
                        "pour consolider la stratégie."
                    ),
                )
            )

        return findings
