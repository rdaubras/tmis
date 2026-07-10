import uuid

from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.issues.schemas import LegalIssue


class HeuristicIssueDetector:
    """Implements `IssueDetectorPort` with two deterministic rules:
    timeline inconsistencies and contested facts each raise a potential
    legal issue for the avocat to review.

    A more sophisticated detector (rule engine, or one that calls
    `TMISKernel.complete()` for a genuinely legal assessment) can replace
    this one behind the same port without touching the rest of the CIE
    (see docs/19-case-intelligence.md).
    """

    def detect(self, profile: CaseProfile) -> list[LegalIssue]:
        issues: list[LegalIssue] = []

        for inconsistency in profile.timeline_inconsistencies:
            issues.append(
                LegalIssue(
                    id=str(uuid.uuid4()),
                    description=(
                        f"Incohérence temporelle détectée pour le {inconsistency.date} : "
                        f"{inconsistency.reason}"
                    ),
                    confidence=0.6,
                )
            )

        for fact in profile.facts:
            if not fact.contradicting_document_ids:
                continue
            issues.append(
                LegalIssue(
                    id=str(uuid.uuid4()),
                    description=f"Fait contesté par au moins un document : {fact.description}",
                    related_fact_ids=(fact.id,),
                    confidence=fact.confidence,
                )
            )

        return issues
