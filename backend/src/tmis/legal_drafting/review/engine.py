import uuid
from collections import defaultdict

from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.review.schemas import ReviewFinding, ReviewFindingType
from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.templates.schemas import TemplateSection
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession

_UNGROUNDED_EXEMPT_ORIGINS = {"template", "style_engine"}


class HeuristicReviewEngine:
    """Implements `ReviewEnginePort` — detects, never corrects (see
    docs/28-legal-drafting.md — Review Engine):

    - **incomplete_section**: a required template section with no
      generated paragraph.
    - **missing_reference**: a kernel-generated paragraph with no
      documentary reference at all (no research result backing it).
    - **unjustified_paragraph**: a kernel-generated paragraph with *no*
      traceability whatsoever (no fact, reference, evidence or
      hypothesis) — a bare, unfounded assertion.
    - **repetition**: two or more paragraphs sharing the exact same
      normalized text.
    - **contradiction**: a paragraph grounded in a fact or hypothesis
      that a Sprint 6 `Conflict` already flags as disputed.
    """

    def review(
        self,
        sections: list[Section],
        template_sections: list[TemplateSection],
        reasoning_session: ReasoningSession | None,
    ) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []
        findings.extend(self._incomplete_sections(sections, template_sections))
        findings.extend(self._paragraph_findings(sections))
        findings.extend(self._repetitions(sections))
        findings.extend(self._contradictions(sections, reasoning_session))
        return findings

    def _incomplete_sections(
        self, sections: list[Section], template_sections: list[TemplateSection]
    ) -> list[ReviewFinding]:
        sections_by_key = {s.key: s for s in sections}
        findings = []
        for template_section in template_sections:
            if not template_section.required:
                continue
            section = sections_by_key.get(template_section.key)
            if section is None or not any(p.text.strip() for p in section.paragraphs):
                findings.append(
                    ReviewFinding(
                        id=str(uuid.uuid4()),
                        type=ReviewFindingType.INCOMPLETE_SECTION,
                        description=f"La section « {template_section.title} » est incomplète.",
                        section_id=section.id if section else None,
                    )
                )
        return findings

    def _paragraph_findings(self, sections: list[Section]) -> list[ReviewFinding]:
        findings = []
        for section in sections:
            for paragraph in section.paragraphs:
                if paragraph.origin in _UNGROUNDED_EXEMPT_ORIGINS:
                    continue
                has_any_grounding = bool(
                    paragraph.fact_ids
                    or paragraph.reference_ids
                    or paragraph.evidence_ids
                    or paragraph.hypothesis_ids
                )
                if not has_any_grounding:
                    findings.append(
                        ReviewFinding(
                            id=str(uuid.uuid4()),
                            type=ReviewFindingType.UNJUSTIFIED_PARAGRAPH,
                            description="Ce paragraphe n'est relié à aucune source.",
                            section_id=section.id,
                            paragraph_id=paragraph.id,
                        )
                    )
                elif not paragraph.reference_ids:
                    findings.append(
                        ReviewFinding(
                            id=str(uuid.uuid4()),
                            type=ReviewFindingType.MISSING_REFERENCE,
                            description="Ce paragraphe n'a aucune référence documentaire.",
                            section_id=section.id,
                            paragraph_id=paragraph.id,
                        )
                    )
        return findings

    def _repetitions(self, sections: list[Section]) -> list[ReviewFinding]:
        by_text: dict[str, list[tuple[Section, Paragraph]]] = defaultdict(list)
        for section in sections:
            for paragraph in section.paragraphs:
                normalized = " ".join(paragraph.text.split()).lower()
                if normalized:
                    by_text[normalized].append((section, paragraph))

        findings = []
        for group in by_text.values():
            if len(group) > 1:
                first_section, first_paragraph = group[0]
                findings.append(
                    ReviewFinding(
                        id=str(uuid.uuid4()),
                        type=ReviewFindingType.REPETITION,
                        description=f"{len(group)} paragraphes partagent un texte identique.",
                        section_id=first_section.id,
                        paragraph_id=first_paragraph.id,
                    )
                )
        return findings

    def _contradictions(
        self, sections: list[Section], reasoning_session: ReasoningSession | None
    ) -> list[ReviewFinding]:
        if reasoning_session is None or not reasoning_session.conflicts:
            return []
        disputed_ids: set[str] = set()
        for conflict in reasoning_session.conflicts:
            disputed_ids.update(conflict.involved_ids)

        findings = []
        for section in sections:
            for paragraph in section.paragraphs:
                touched = disputed_ids & (set(paragraph.fact_ids) | set(paragraph.hypothesis_ids))
                if touched:
                    findings.append(
                        ReviewFinding(
                            id=str(uuid.uuid4()),
                            type=ReviewFindingType.CONTRADICTION,
                            description=(
                                "Ce paragraphe s'appuie sur un élément signalé "
                                "comme contesté par le Legal Reasoning Engine."
                            ),
                            section_id=section.id,
                            paragraph_id=paragraph.id,
                        )
                    )
        return findings
