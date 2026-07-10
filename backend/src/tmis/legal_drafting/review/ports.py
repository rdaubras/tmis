from typing import Protocol

from tmis.legal_drafting.review.schemas import ReviewFinding
from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.templates.schemas import TemplateSection
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession


class ReviewEnginePort(Protocol):
    """Port implemented by every interchangeable review engine. Only
    ever reports findings — it never rewrites a section or a paragraph
    itself (see docs/28-legal-drafting.md — Review Engine)."""

    def review(
        self,
        sections: list[Section],
        template_sections: list[TemplateSection],
        reasoning_session: ReasoningSession | None,
    ) -> list[ReviewFinding]: ...
