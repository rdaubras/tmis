class GuardrailViolation(Exception):
    """Raised when an input fails a hard guardrail check.

    Output guardrails deliberately do *not* raise: like the Verifier agent
    (see docs/05-strategie-multi-agents.md), they surface warnings instead
    of blocking a response, since the avocat must stay in control of the
    decision.
    """

    def __init__(self, guardrail_name: str, message: str) -> None:
        super().__init__(f"[{guardrail_name}] {message}")
        self.guardrail_name = guardrail_name
