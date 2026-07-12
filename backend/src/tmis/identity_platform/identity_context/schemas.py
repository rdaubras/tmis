from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class IdentityContext:
    """The business profile associated with an authenticated user for
    the duration of a request — "chaque profil contient : spécialité
    juridique, niveau d'expérience, équipe, langue, préférences
    rédactionnelles, modèles IA autorisés, droits de validation,
    politiques applicables" (sprint requirement). AI agents read this
    to adapt their proposals; `authorization.AuthorizationEngine`
    reads it for ABAC evaluation."""

    user_id: str
    firm_id: str
    specialty: str = ""
    experience_level: str = ""
    seniority_years: int = 0
    team_id: str | None = None
    department_id: str | None = None
    language: str = "fr"
    writing_preferences: dict[str, str] = field(default_factory=dict)
    allowed_ai_models: tuple[str, ...] = ()
    can_validate: bool = False
    applicable_policy_ids: tuple[str, ...] = ()
