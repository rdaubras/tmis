"""The core `Workflow` aggregate — versioned, per the sprint's "les
workflows sont versionnés" requirement.

Naming note: this is the fourth "Workflow"-shaped concept in TMIS —
`case_intelligence.workflow.CaseIntelligenceWorkflow` (the living-case
orchestrator, Sprint 4), `collaboration.workflow.ConfigurableWorkflowEngine`
(a per-task Kanban-style status lifecycle, Sprint 8), and this one (a
business-process-automation definition: triggers/conditions/steps/
actions). Same role name, three unrelated scopes — documented
explicitly rather than renamed, following the project's established
naming-collision convention (see docs/09, rule 15).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from tmis.workflow_automation.action_engine.schemas import Action
from tmis.workflow_automation.condition_engine.schemas import Condition
from tmis.workflow_automation.trigger_engine.schemas import Trigger


class WorkflowStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


def new_workflow_id() -> str:
    return f"wf-{uuid.uuid4().hex[:12]}"


def new_workflow_key() -> str:
    return f"wfkey-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    """One step of the workflow — an action, optionally gated by its
    own condition, executed in `order`. `parallel_group` steps sharing
    the same non-null value are eligible for parallel execution by
    `execution_engine` (steps with a null group run sequentially)."""

    order: int
    name: str
    action: Action
    condition: Condition | None = None
    parallel_group: str | None = None


@dataclass(slots=True)
class Workflow:
    """One version of a workflow definition. `workflow_key` is stable
    across versions of "the same" workflow; `id` and `version` are
    unique to this snapshot — mirrors
    `legal_drafting.versioning.DocumentVersion`'s
    `document_id`/`version_number` split."""

    id: str
    workflow_key: str
    firm_id: str
    name: str
    version: int
    owner: str
    description: str = ""
    triggers: tuple[Trigger, ...] = field(default_factory=tuple)
    conditions: tuple[Condition, ...] = field(default_factory=tuple)
    steps: tuple[WorkflowStep, ...] = field(default_factory=tuple)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
