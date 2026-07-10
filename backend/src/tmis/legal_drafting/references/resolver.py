import uuid

from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.references.schemas import ReferenceLink, ReferenceTargetType
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_research.search.schemas import ResearchResult


class HeuristicReferenceResolver:
    """Implements `ReferenceResolverPort`: turns the raw ids a
    `Paragraph` carries (`fact_ids`, `reference_ids`, `evidence_ids`,
    `hypothesis_ids`) into fully resolved, human-readable
    `ReferenceLink` objects by looking them up in the upstream engines'
    own data — never re-deriving anything, only relabeling (see
    docs/28-legal-drafting.md — Paragraph Engine)."""

    def resolve(
        self,
        paragraph: Paragraph,
        *,
        facts: list[Fact],
        research_results: list[ResearchResult],
        reasoning_session: ReasoningSession | None,
    ) -> list[ReferenceLink]:
        facts_by_id = {f.id: f for f in facts}
        results_by_id = {r.id: r for r in research_results}
        evidence_by_id = (
            {e.id: e for e in reasoning_session.evidence_links} if reasoning_session else {}
        )
        hypotheses_by_id = (
            {h.id: h for h in reasoning_session.hypotheses} if reasoning_session else {}
        )

        links: list[ReferenceLink] = []
        for fact_id in paragraph.fact_ids:
            fact = facts_by_id.get(fact_id)
            if fact is not None:
                links.append(
                    ReferenceLink(
                        id=str(uuid.uuid4()),
                        target_type=ReferenceTargetType.FACT,
                        target_id=fact.id,
                        label=fact.description,
                        excerpt=fact.description,
                    )
                )
        for result_id in paragraph.reference_ids:
            result = results_by_id.get(result_id)
            if result is not None:
                links.append(
                    ReferenceLink(
                        id=str(uuid.uuid4()),
                        target_type=ReferenceTargetType.RESEARCH_RESULT,
                        target_id=result.id,
                        label=result.title,
                        excerpt=result.excerpt,
                    )
                )
        for evidence_id in paragraph.evidence_ids:
            evidence = evidence_by_id.get(evidence_id)
            if evidence is not None:
                links.append(
                    ReferenceLink(
                        id=str(uuid.uuid4()),
                        target_type=ReferenceTargetType.EVIDENCE,
                        target_id=evidence.id,
                        label=f"Preuve (fiabilité {evidence.reliability_score:.2f})",
                        excerpt=evidence.fact_id or "",
                    )
                )
        for hypothesis_id in paragraph.hypothesis_ids:
            hypothesis = hypotheses_by_id.get(hypothesis_id)
            if hypothesis is not None:
                links.append(
                    ReferenceLink(
                        id=str(uuid.uuid4()),
                        target_type=ReferenceTargetType.HYPOTHESIS,
                        target_id=hypothesis.id,
                        label=hypothesis.description,
                        excerpt=hypothesis.description,
                    )
                )
        return links
