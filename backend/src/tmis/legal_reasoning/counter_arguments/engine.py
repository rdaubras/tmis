import uuid

from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_research.search.schemas import ResearchResult

_CASE_FACTS_CONNECTOR = "case_facts"


class HeuristicCounterArgumentEngine:
    """Implements `CounterArgumentEnginePort`: for each argument, looks
    first for a case fact that already contradicts one of the fact ids
    its hypothesis relies on (reusing the contradiction detection the
    Case Intelligence Engine already computed in `Fact.contradicting_document_ids`,
    Sprint 4) — the strongest, most traceable kind of counter-argument.
    Failing that, it falls back to a research result from a different
    connector than the argument's own, as a contrasting viewpoint worth
    confronting (see docs/25-legal-reasoning.md — Counter Argument Engine).
    """

    def build(
        self,
        arguments: list[Argument],
        hypotheses: list[Hypothesis],
        facts: list[Fact],
        research_results: list[ResearchResult],
    ) -> list[CounterArgument]:
        hypotheses_by_id = {h.id: h for h in hypotheses}
        facts_by_id = {f.id: f for f in facts}
        counters: list[CounterArgument] = []

        for argument in arguments:
            hypothesis = hypotheses_by_id.get(argument.hypothesis_id)
            counter = self._contradicting_fact_counter(argument, hypothesis, facts_by_id)
            if counter is None:
                counter = self._contrasting_source_counter(argument, research_results)
            if counter is not None:
                counters.append(counter)
        return counters

    def _contradicting_fact_counter(
        self,
        argument: Argument,
        hypothesis: Hypothesis | None,
        facts_by_id: dict[str, Fact],
    ) -> CounterArgument | None:
        if hypothesis is None:
            return None
        for fact_id in hypothesis.supporting_fact_ids:
            fact = facts_by_id.get(fact_id)
            if fact is not None and fact.contradicting_document_ids:
                return CounterArgument(
                    id=str(uuid.uuid4()),
                    argument_id=argument.id,
                    claim=(
                        f"Le fait « {fact.description} » est contredit par "
                        f"{len(fact.contradicting_document_ids)} document(s) du dossier."
                    ),
                    source_connector=_CASE_FACTS_CONNECTOR,
                    source_reference=fact.id,
                    excerpt=fact.description,
                    confidence=1.0 - fact.confidence,
                )
        return None

    def _contrasting_source_counter(
        self, argument: Argument, research_results: list[ResearchResult]
    ) -> CounterArgument | None:
        alternative = next(
            (r for r in research_results if r.connector != argument.source_connector), None
        )
        if alternative is None:
            return None
        return CounterArgument(
            id=str(uuid.uuid4()),
            argument_id=argument.id,
            claim=(
                f"Un point de vue distinct issu de « {alternative.title} » "
                "mérite d'être confronté à cet argument."
            ),
            source_connector=alternative.connector,
            source_reference=alternative.reference,
            excerpt=alternative.excerpt,
            confidence=alternative.final_score,
        )
