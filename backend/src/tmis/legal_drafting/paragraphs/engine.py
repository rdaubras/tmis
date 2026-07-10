import uuid

from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_drafting.paragraphs.ports import DraftingKernelPort
from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.style.engine import StyleEngine
from tmis.legal_drafting.style.ports import StyleEnginePort
from tmis.legal_drafting.style.schemas import StyleProfile
from tmis.legal_drafting.templates.schemas import SectionRole, TemplateSection
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_research.search.schemas import ResearchResult

_MAX_FACTS_PER_PARAGRAPH = 5
_MAX_RESEARCH_RESULTS_PER_PARAGRAPH = 3

_ContentResult = tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]


class HeuristicParagraphEngine:
    """Implements `ParagraphEnginePort`: one paragraph per section role,
    each grounded in exactly the pieces of context declared in its id
    fields — a paragraph never claims traceability wider than what was
    actually fed into its generation (see docs/28-legal-drafting.md —
    Paragraph Engine). `header` and `signature` are deterministic
    boilerplate (no model call); every other role goes through
    `TMISKernel.complete()` — the only LLM call in the whole Legal
    Drafting Studio.
    """

    def __init__(
        self, kernel: DraftingKernelPort, style_engine: StyleEnginePort | None = None
    ) -> None:
        self._kernel = kernel
        self._style_engine: StyleEnginePort = style_engine or StyleEngine()

    async def generate(
        self,
        template_section: TemplateSection,
        *,
        facts: list[Fact],
        research_results: list[ResearchResult],
        reasoning_session: ReasoningSession | None,
        style_profile: StyleProfile,
        variables: dict[str, str],
    ) -> list[Paragraph]:
        if template_section.role == SectionRole.HEADER:
            return [self._header_paragraph(template_section, variables)]
        if template_section.role == SectionRole.SIGNATURE:
            return [self._signature_paragraph(template_section, variables, style_profile)]

        text, fact_ids, reference_ids, evidence_ids, hypothesis_ids = await self._generate_content(
            template_section, facts, research_results, reasoning_session, style_profile
        )
        return [
            Paragraph(
                id=str(uuid.uuid4()),
                section_key=template_section.key,
                order=0,
                text=text,
                origin="kernel",
                fact_ids=fact_ids,
                reference_ids=reference_ids,
                evidence_ids=evidence_ids,
                hypothesis_ids=hypothesis_ids,
            )
        ]

    async def regenerate_one(
        self,
        paragraph: Paragraph,
        template_section: TemplateSection,
        *,
        facts: list[Fact],
        research_results: list[ResearchResult],
        reasoning_session: ReasoningSession | None,
        style_profile: StyleProfile,
        variables: dict[str, str],
    ) -> Paragraph:
        regenerated = await self.generate(
            template_section,
            facts=facts,
            research_results=research_results,
            reasoning_session=reasoning_session,
            style_profile=style_profile,
            variables=variables,
        )
        new_paragraph = regenerated[0]
        new_paragraph.id = paragraph.id
        new_paragraph.order = paragraph.order
        return new_paragraph

    def _header_paragraph(
        self, template_section: TemplateSection, variables: dict[str, str]
    ) -> Paragraph:
        firm = variables.get("firm_name", "Cabinet")
        client = variables.get("client_name", "Client")
        reference = variables.get("case_reference", "")
        text = f"{firm} — {template_section.title} — {client}"
        if reference:
            text += f" (réf. {reference})"
        return Paragraph(
            id=str(uuid.uuid4()),
            section_key=template_section.key,
            order=0,
            text=text,
            origin="template",
        )

    def _signature_paragraph(
        self,
        template_section: TemplateSection,
        variables: dict[str, str],
        style_profile: StyleProfile,
    ) -> Paragraph:
        firm = variables.get("firm_name", "Cabinet")
        closing = self._style_engine.closing_formula(style_profile)
        text = f"{closing}\n{firm}"
        return Paragraph(
            id=str(uuid.uuid4()),
            section_key=template_section.key,
            order=0,
            text=text,
            origin="style_engine",
        )

    async def _generate_content(
        self,
        template_section: TemplateSection,
        facts: list[Fact],
        research_results: list[ResearchResult],
        reasoning_session: ReasoningSession | None,
        style_profile: StyleProfile,
    ) -> _ContentResult:
        style_instructions = self._style_engine.prompt_instructions(style_profile)

        if template_section.role == SectionRole.FACTS:
            return await self._facts_content(template_section, facts, style_instructions)
        if template_section.role in (SectionRole.LEGAL_DISCUSSION, SectionRole.ARGUMENTS):
            return await self._discussion_content(
                template_section, research_results, reasoning_session, style_instructions
            )
        if template_section.role == SectionRole.RECOMMENDATIONS:
            return await self._recommendations_content(
                template_section, reasoning_session, style_instructions
            )
        return await self._generic_content(template_section, reasoning_session, style_instructions)

    async def _facts_content(
        self, template_section: TemplateSection, facts: list[Fact], style_instructions: str
    ) -> _ContentResult:
        selected = facts[:_MAX_FACTS_PER_PARAGRAPH]
        facts_text = "; ".join(f.description for f in selected) or "aucun fait consolidé disponible"
        prompt = (
            f"Rédige, {style_instructions}, un paragraphe d'exposé des faits pour la section "
            f"« {template_section.title} », à partir strictement des faits suivants : {facts_text}."
        )
        response = await self._kernel.complete(prompt)
        return response.text, tuple(f.id for f in selected), (), (), ()

    async def _discussion_content(
        self,
        template_section: TemplateSection,
        research_results: list[ResearchResult],
        reasoning_session: ReasoningSession | None,
        style_instructions: str,
    ) -> _ContentResult:
        selected_results = research_results[:_MAX_RESEARCH_RESULTS_PER_PARAGRAPH]
        references_text = "; ".join(f"{r.title} ({r.reference})" for r in selected_results) or (
            "aucune référence documentaire disponible"
        )
        hypotheses = reasoning_session.hypotheses if reasoning_session else []
        hypotheses_text = "; ".join(h.description for h in hypotheses) or (
            "aucune hypothèse disponible"
        )
        prompt = (
            f"Rédige, {style_instructions}, un paragraphe de « {template_section.title} », en "
            f"t'appuyant sur les hypothèses suivantes : {hypotheses_text}, et sur les références "
            f"suivantes : {references_text}."
        )
        response = await self._kernel.complete(prompt)
        hypothesis_ids = {h.id for h in hypotheses}
        evidence_ids = tuple(
            e.id
            for e in (reasoning_session.evidence_links if reasoning_session else [])
            if e.hypothesis_id in hypothesis_ids
        )
        return (
            response.text,
            (),
            tuple(r.id for r in selected_results),
            evidence_ids,
            tuple(hypothesis_ids),
        )

    async def _recommendations_content(
        self,
        template_section: TemplateSection,
        reasoning_session: ReasoningSession | None,
        style_instructions: str,
    ) -> _ContentResult:
        strategies = reasoning_session.strategies if reasoning_session else []
        strategies_text = "; ".join(s.objective for s in strategies) or "aucune piste disponible"
        prompt = (
            f"Rédige, {style_instructions}, un paragraphe de recommandations à partir de : "
            f"{strategies_text}."
        )
        response = await self._kernel.complete(prompt)
        hypothesis_ids = tuple({s.hypothesis_id for s in strategies})
        return response.text, (), (), (), hypothesis_ids

    async def _generic_content(
        self,
        template_section: TemplateSection,
        reasoning_session: ReasoningSession | None,
        style_instructions: str,
    ) -> _ContentResult:
        raw_synthesis = reasoning_session.synthesis if reasoning_session else ""
        synthesis = raw_synthesis or "aucune synthèse disponible"
        prompt = (
            f"Rédige, {style_instructions}, un paragraphe de « {template_section.title} » en te "
            f"fondant sur la synthèse suivante : {synthesis}."
        )
        response = await self._kernel.complete(prompt)
        return response.text, (), (), (), ()
