from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AbacAttributes:
    """Request-specific attributes an ABAC rule may condition on —
    "du dossier, du client, du niveau de confidentialité, de
    l'ancienneté, du contexte d'utilisation" (sprint requirement).
    Seniority and department come from `IdentityContext`/`roles`, not
    duplicated here."""

    department_id: str | None = None
    case_id: str | None = None
    client_id: str | None = None
    confidentiality_level: str = "standard"
    context: str = ""
