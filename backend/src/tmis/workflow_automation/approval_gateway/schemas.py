from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApprovalPolicy:
    """Whether a given action type requires human validation before
    it runs, per cabinet — "les politiques de validation sont
    configurables" (sprint requirement)."""

    firm_id: str
    action_type: str
    required: bool = True
