from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.facts.schemas import Fact
from tmis.case_intelligence.issues.heuristic_detector import HeuristicIssueDetector
from tmis.case_intelligence.timeline.schemas import CaseTimelineEntry, TimelineInconsistency


def test_detects_no_issue_on_a_clean_profile() -> None:
    profile = CaseProfile(case_id="case-1", title="Test")
    assert HeuristicIssueDetector().detect(profile) == []


def test_detects_issue_for_timeline_inconsistency() -> None:
    profile = CaseProfile(case_id="case-1", title="Test")
    entry_a = CaseTimelineEntry(
        date="1 janvier 2020", description="A", document_ids=("d1",), confidence=0.6
    )
    entry_b = CaseTimelineEntry(
        date="1 janvier 2020", description="B", document_ids=("d2",), confidence=0.6
    )
    profile.timeline_inconsistencies = [
        TimelineInconsistency(date="1 janvier 2020", entries=(entry_a, entry_b))
    ]

    issues = HeuristicIssueDetector().detect(profile)

    assert len(issues) == 1
    assert "1 janvier 2020" in issues[0].description


def test_detects_issue_for_contested_fact() -> None:
    profile = CaseProfile(case_id="case-1", title="Test")
    profile.facts = [
        Fact(
            id="f1",
            description="Résiliation",
            confidence=0.6,
            contradicting_document_ids={"doc-2"},
        )
    ]

    issues = HeuristicIssueDetector().detect(profile)

    assert len(issues) == 1
    assert issues[0].related_fact_ids == ("f1",)


def test_does_not_raise_issue_for_uncontested_fact() -> None:
    profile = CaseProfile(case_id="case-1", title="Test")
    profile.facts = [Fact(id="f1", description="Signature", confidence=0.6)]
    assert HeuristicIssueDetector().detect(profile) == []
