from tmis.ai.schemas.agent import AgentOutput


class CitationsTraceableGuardrail:
    """Flags any citation claimed by an agent that does not carry a
    traceable excerpt and reference (see docs/06-strategie-rag.md)."""

    name = "citations_traceable"

    def validate(self, output: AgentOutput) -> list[str]:
        warnings = []
        for citation in output.citations:
            if not citation.excerpt or not citation.reference:
                warnings.append(
                    f"[{self.name}] Citation {citation.source_id!r} is missing a "
                    "traceable excerpt or reference."
                )
        return warnings


class NonEmptyResultGuardrail:
    """Flags an `AgentOutput` whose `result` is empty, which usually means
    the agent had nothing to say and the caller should not present it as a
    confident answer."""

    name = "non_empty_result"

    def validate(self, output: AgentOutput) -> list[str]:
        if not output.result:
            return [f"[{self.name}] Result payload is empty."]
        return []
