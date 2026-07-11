from enum import StrEnum


class ExtensionPermission(StrEnum):
    """The fixed, explicit vocabulary of what an extension may be
    granted (see the sprint's "PERMISSION ENGINE" spec) — deliberately
    a closed enum, not a free-form string, so
    `tmis.platform_sdk.validation` can reject a manifest that declares
    an unknown permission."""

    READ_CASES = "read_cases"
    READ_DOCUMENTS = "read_documents"
    CREATE_DRAFTS = "create_drafts"
    ACCESS_RESEARCH = "access_research"
    ACCESS_KNOWLEDGE = "access_knowledge"
    MANAGE_USERS = "manage_users"
