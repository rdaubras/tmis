from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.decision_graph.schemas import (
    DecisionEdge,
    DecisionGraph,
    DecisionNode,
    DecisionNodeType,
)
from tmis.legal_reasoning.evidence.schemas import ReasoningEvidenceLink
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis

_QUESTION_NODE_ID = "question"
_SYNTHESIS_NODE_ID = "synthesis"


class ChainDecisionGraphBuilder:
    """Implements `DecisionGraphBuilderPort`: lays out the reasoning run
    as the chain Question -> Hypotheses -> Arguments -> Counter-arguments
    -> Evidence -> References -> Synthesis, ready for the UI to render
    (see docs/25-legal-reasoning.md — Decision Graph)."""

    def build(
        self,
        question: str,
        hypotheses: list[Hypothesis],
        arguments: list[Argument],
        counter_arguments: list[CounterArgument],
        evidence_links: list[ReasoningEvidenceLink],
        references: list[str],
        synthesis: str,
    ) -> DecisionGraph:
        nodes: list[DecisionNode] = [
            DecisionNode(_QUESTION_NODE_ID, DecisionNodeType.QUESTION, question)
        ]
        edges: list[DecisionEdge] = []

        for hypothesis in hypotheses:
            hyp_node_id = f"hypothesis:{hypothesis.id}"
            nodes.append(
                DecisionNode(hyp_node_id, DecisionNodeType.HYPOTHESIS, hypothesis.description)
            )
            edges.append(DecisionEdge(_QUESTION_NODE_ID, hyp_node_id, "considers"))

        for argument in arguments:
            arg_node_id = f"argument:{argument.id}"
            hyp_node_id = f"hypothesis:{argument.hypothesis_id}"
            nodes.append(DecisionNode(arg_node_id, DecisionNodeType.ARGUMENT, argument.claim))
            edges.append(DecisionEdge(hyp_node_id, arg_node_id, "supported_by"))

        for counter in counter_arguments:
            counter_node_id = f"counter_argument:{counter.id}"
            arg_node_id = f"argument:{counter.argument_id}"
            nodes.append(
                DecisionNode(counter_node_id, DecisionNodeType.COUNTER_ARGUMENT, counter.claim)
            )
            edges.append(DecisionEdge(arg_node_id, counter_node_id, "challenged_by"))

        for evidence_link in evidence_links:
            if evidence_link.hypothesis_id is None:
                continue
            evidence_node_id = f"evidence:{evidence_link.id}"
            hyp_node_id = f"hypothesis:{evidence_link.hypothesis_id}"
            label = f"Preuve (fiabilité {evidence_link.reliability_score:.2f})"
            nodes.append(DecisionNode(evidence_node_id, DecisionNodeType.EVIDENCE, label))
            edges.append(DecisionEdge(hyp_node_id, evidence_node_id, "grounded_by"))

        for index, reference in enumerate(references):
            reference_node_id = f"reference:{index}"
            nodes.append(DecisionNode(reference_node_id, DecisionNodeType.REFERENCE, reference))
            edges.append(DecisionEdge(_QUESTION_NODE_ID, reference_node_id, "cites"))

        nodes.append(DecisionNode(_SYNTHESIS_NODE_ID, DecisionNodeType.SYNTHESIS, synthesis))
        for hypothesis in hypotheses:
            edges.append(
                DecisionEdge(f"hypothesis:{hypothesis.id}", _SYNTHESIS_NODE_ID, "feeds_into")
            )

        return DecisionGraph(nodes=tuple(nodes), edges=tuple(edges))
