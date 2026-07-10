import re
import uuid

from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_research.search.schemas import ResearchResult

_TOKEN_RE = re.compile(r"[a-zà-ÿ]+", re.IGNORECASE)


class HeuristicArgumentEngine:
    """Implements `ArgumentEnginePort`: for each hypothesis, turns every
    research result whose content overlaps with the hypothesis'
    description into a supporting `Argument`, keeping the connector,
    reference and excerpt it came from (see docs/25-legal-reasoning.md —
    Argument Engine). A result can support more than one hypothesis.
    """

    def build(
        self, hypotheses: list[Hypothesis], research_results: list[ResearchResult]
    ) -> list[Argument]:
        arguments: list[Argument] = []
        for hypothesis in hypotheses:
            keywords = {t.lower() for t in _TOKEN_RE.findall(hypothesis.description) if len(t) > 2}
            for result in research_results:
                haystack = f"{result.title} {result.excerpt}".lower()
                if not any(keyword in haystack for keyword in keywords):
                    continue
                arguments.append(
                    Argument(
                        id=str(uuid.uuid4()),
                        hypothesis_id=hypothesis.id,
                        claim=f"« {result.title} » soutient : {hypothesis.description}",
                        source_connector=result.connector,
                        source_reference=result.reference,
                        excerpt=result.excerpt,
                        confidence=result.final_score,
                    )
                )
        return arguments
