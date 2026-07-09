from tmis.agents.contracts import AgentInput, AgentOutput, ConfidenceLevel


class VerifierAgent:
    """Checks coherence, citations, contradictions and duplicates (docs/05).

    Every other agent's output is routed through this agent before the
    orchestrator fuses a final response. In Sprint 1 it performs the one
    check that is always meaningful regardless of which specialized agent
    ran: that any citation claimed actually carries a traceable reference.
    Deeper coherence/contradiction analysis is scheduled for Sprint 13.
    """

    name = "verifier"

    async def verify(self, output: AgentOutput) -> AgentOutput:
        warnings = list(output.warnings)
        for citation in output.citations:
            if not citation.excerpt or not citation.reference:
                warnings.append(
                    f"Citation {citation.source_id!r} is missing a traceable excerpt or reference."
                )

        confidence = output.confidence
        if warnings and confidence == ConfidenceLevel.HIGH:
            confidence = ConfidenceLevel.MEDIUM

        return AgentOutput(
            result=output.result,
            citations=output.citations,
            confidence=confidence,
            warnings=warnings,
        )

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "VerifierAgent is invoked via `verify(output)` on another agent's output, "
            "not directly as a graph entry point."
        )
