import uuid

from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.evidence.schemas import ReasoningEvidenceLink
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis


class HeuristicEvidenceEngine:
    """Implements `EvidenceEnginePort`: for every fact a hypothesis relies
    on, emits one `ReasoningEvidenceLink` per source document, scored by
    reliability (how much a fact is corroborated versus contradicted —
    reusing the CIE's `Fact.confirming_document_ids`/
    `contradicting_document_ids`, Sprint 4). Any argument built from that
    same hypothesis is attached to the link too, so evidence stays
    traceable to facts, documents, hypotheses *and* arguments at once
    (see docs/25-legal-reasoning.md — Evidence Engine).
    """

    def link(
        self,
        hypotheses: list[Hypothesis],
        arguments: list[Argument],
        facts: list[Fact],
    ) -> list[ReasoningEvidenceLink]:
        facts_by_id = {f.id: f for f in facts}
        arguments_by_hypothesis: dict[str, list[Argument]] = {}
        for argument in arguments:
            arguments_by_hypothesis.setdefault(argument.hypothesis_id, []).append(argument)

        links: list[ReasoningEvidenceLink] = []
        for hypothesis in hypotheses:
            related_arguments = arguments_by_hypothesis.get(hypothesis.id, [])
            argument_id = related_arguments[0].id if related_arguments else None
            for fact_id in hypothesis.supporting_fact_ids:
                fact = facts_by_id.get(fact_id)
                if fact is None:
                    continue
                reliability = self._reliability(fact)
                document_ids: set[str | None] = (
                    set(fact.source_document_ids) if fact.source_document_ids else {None}
                )
                for document_id in document_ids:
                    links.append(
                        ReasoningEvidenceLink(
                            id=str(uuid.uuid4()),
                            fact_id=fact.id,
                            document_id=document_id,
                            hypothesis_id=hypothesis.id,
                            argument_id=argument_id,
                            reliability_score=reliability,
                        )
                    )
        return links

    def _reliability(self, fact: Fact) -> float:
        confirming = len(fact.confirming_document_ids)
        contradicting = len(fact.contradicting_document_ids)
        corroboration = (1 + confirming) / (1 + confirming + contradicting)
        return max(0.0, min(1.0, fact.confidence * corroboration))
