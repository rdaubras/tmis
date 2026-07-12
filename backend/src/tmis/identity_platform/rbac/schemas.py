from tmis.identity_platform.permissions.schemas import Permission
from tmis.identity_platform.roles.schemas import Role

DEFAULT_ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.PARTNER: frozenset(
        {
            Permission.CONSULTATION_VALIDATE,
            Permission.AI_MODEL_RESTRICTED_USE,
            Permission.EXPORT_DATA,
            Permission.STRATEGY_DRAFT_VALIDATE,
            Permission.WORKFLOW_USE_TEAM_RESTRICTED,
            Permission.ORGANIZATION_MANAGE,
            Permission.USER_MANAGE,
            Permission.BUSINESS_PLATFORM_MANAGE,
        }
    ),
    Role.ASSOCIATE: frozenset(
        {
            Permission.EXPORT_DATA,
            Permission.WORKFLOW_USE_TEAM_RESTRICTED,
        }
    ),
    Role.COUNSEL: frozenset({Permission.EXPORT_DATA}),
    Role.PARALEGAL: frozenset(),
    Role.ASSISTANT: frozenset(),
    Role.IT_ADMIN: frozenset(
        {
            Permission.ORGANIZATION_MANAGE,
            Permission.SECRET_MANAGE,
            Permission.BUSINESS_PLATFORM_MANAGE,
        }
    ),
}
