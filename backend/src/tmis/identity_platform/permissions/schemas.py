from enum import StrEnum


class Permission(StrEnum):
    """Firm-wide, cross-module permission vocabulary — distinct scope
    from `collaboration.permissions.Permission` (workspace-scoped,
    Sprint 8), on the same architectural-role/different-scope
    principle as `roles.Role`. Named after the sprint's own examples
    ("seuls les associés peuvent valider une consultation", "certains
    modèles IA sont réservés aux associés", "l'export est interdit
    pour certains rôles"...)."""

    CONSULTATION_VALIDATE = "consultation.validate"
    AI_MODEL_RESTRICTED_USE = "ai_model.restricted_use"
    EXPORT_DATA = "export.data"
    STRATEGY_DRAFT_VALIDATE = "strategy_draft.validate"
    WORKFLOW_USE_TEAM_RESTRICTED = "workflow.use_team_restricted"
    ORGANIZATION_MANAGE = "organization.manage"
    USER_MANAGE = "user.manage"
    SECRET_MANAGE = "secret.manage"
    BUSINESS_PLATFORM_MANAGE = "business_platform.manage"
    COPILOT_MANAGE = "copilot.manage"
