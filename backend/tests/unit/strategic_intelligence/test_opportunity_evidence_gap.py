from tmis.strategic_intelligence.evidence_gap.engine import EvidenceGapEngine
from tmis.strategic_intelligence.opportunity_engine.engine import OpportunityEngine


def test_opportunity_engine_flags_unused_hypotheses() -> None:
    engine = OpportunityEngine()

    findings = engine.find(
        "strategy-1",
        main_arguments=("a", "b"),
        unused_hypotheses=("Discrimination syndicale",),
    )

    assert any(f.category == "argument_inexploité" for f in findings)


def test_opportunity_engine_every_finding_is_justified() -> None:
    engine = OpportunityEngine()

    findings = engine.find(
        "strategy-1",
        missing_evidence=("Témoignage",),
        clauses_to_verify=("Clause X",),
    )

    for finding in findings:
        assert finding.justification


def test_opportunity_engine_flags_additional_research_when_few_arguments() -> None:
    engine = OpportunityEngine()

    findings = engine.find("strategy-1", main_arguments=("un seul",))

    assert any(f.category == "recherche_additionnelle" for f in findings)


def test_opportunity_engine_no_extra_research_flag_with_enough_arguments() -> None:
    engine = OpportunityEngine()

    findings = engine.find("strategy-1", main_arguments=("a", "b", "c"))

    assert not any(f.category == "recherche_additionnelle" for f in findings)


def test_evidence_gap_engine_produces_one_gap_per_missing_item() -> None:
    engine = EvidenceGapEngine()

    gaps = engine.identify("strategy-1", ("Témoignage", "Relevé horaires", "Contrat"))

    assert len(gaps) == 3
    for gap in gaps:
        assert gap.interest
        assert gap.potential_impact


def test_evidence_gap_engine_ranks_earlier_items_as_higher_impact() -> None:
    engine = EvidenceGapEngine()

    gaps = engine.identify(
        "strategy-1", ("Priorité 1", "Priorité 2", "Priorité 3", "Priorité 4", "Priorité 5")
    )

    assert "élevé" in gaps[0].potential_impact
    assert "faible" in gaps[-1].potential_impact
