from enum import Enum


class WorkflowStatus(str, Enum):
    """The six stages the Sprint 8 prompt asks for (see
    docs/36-guide-workflows.md)."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    TO_VALIDATE = "to_validate"
    VALIDATED = "validated"
    ARCHIVED = "archived"
