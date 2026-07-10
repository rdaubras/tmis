import re
import uuid

from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_research.search.schemas import ResearchResult

_TOKEN_RE = re.compile(r"[a-zà-ÿ]+", re.IGNORECASE)
_MAX_REFERENCES = 5


class HeuristicHypothesisEngine:
    """Implements `HypothesisEnginePort`: always proposes at least two
    co-existing hypotheses — one affirmative reading of the question, one
    contrary reading — each grounded in the case facts that share
    keywords with the question and cited against the top research
    results (see docs/25-legal-reasoning.md — Hypothesis Engine).

    A richer engine (calling `TMISKernel.complete()` for genuinely novel
    hypotheses) can replace this behind the same port without touching
    the orchestrator.
    """

    def generate(
        self, question: str, facts: list[Fact], research_results: list[ResearchResult]
    ) -> list[Hypothesis]:
        keywords = {t.lower() for t in _TOKEN_RE.findall(question) if len(t) > 2}
        supporting_fact_ids = tuple(
            f.id for f in facts if keywords & {t.lower() for t in _TOKEN_RE.findall(f.description)}
        )
        references = tuple(r.reference for r in research_results[:_MAX_REFERENCES])
        stripped_question = question.strip().rstrip("?").strip()

        return [
            Hypothesis(
                id=str(uuid.uuid4()),
                description=f"Hypothèse favorable : {stripped_question} est fondé.",
                supporting_fact_ids=supporting_fact_ids,
                references=references,
                confidence=0.5,
            ),
            Hypothesis(
                id=str(uuid.uuid4()),
                description=f"Hypothèse contraire : {stripped_question} n'est pas fondé.",
                supporting_fact_ids=(),
                references=references,
                confidence=0.3,
            ),
        ]
