from typing import TYPE_CHECKING, Protocol

from tmis.case_intelligence.issues.schemas import LegalIssue

if TYPE_CHECKING:
    from tmis.case_intelligence.cases.schemas import CaseProfile


class IssueDetectorPort(Protocol):
    """Port implemented by every interchangeable legal-issue detection
    engine (see docs/19-case-intelligence.md)."""

    def detect(self, profile: "CaseProfile") -> list[LegalIssue]: ...
