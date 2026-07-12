from tmis.identity_platform.abac.schemas import AbacAttributes
from tmis.identity_platform.identity_context.schemas import IdentityContext

_CONFIDENTIALITY_RANK = {"standard": 0, "confidential": 1, "privileged": 2}


class MinimumSeniorityRule:
    """Denies unless `identity.seniority_years >= min_years` — "de
    l'ancienneté" (sprint requirement)."""

    def __init__(self, min_years: int) -> None:
        self._min_years = min_years

    def evaluate(self, identity: IdentityContext, attributes: AbacAttributes) -> bool:
        return identity.seniority_years >= self._min_years


class ConfidentialityRule:
    """Denies unless the identity's `experience_level` clears the
    resource's `confidentiality_level` — a junior profile can never
    touch a `privileged` matter regardless of role."""

    def __init__(self, min_experience_rank: dict[str, int]) -> None:
        self._min_experience_rank = min_experience_rank

    def evaluate(self, identity: IdentityContext, attributes: AbacAttributes) -> bool:
        required_rank = _CONFIDENTIALITY_RANK.get(attributes.confidentiality_level, 0)
        actual_rank = self._min_experience_rank.get(identity.experience_level, 0)
        return actual_rank >= required_rank


class SameDepartmentRule:
    """Denies unless the identity and the resource belong to the same
    department (or the resource does not scope to a department at
    all) — "du dossier, du client... du contexte" (sprint
    requirement)."""

    def evaluate(self, identity: IdentityContext, attributes: AbacAttributes) -> bool:
        if attributes.department_id is None:
            return True
        return identity.department_id == attributes.department_id
