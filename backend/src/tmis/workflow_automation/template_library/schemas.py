import uuid
from dataclasses import dataclass, field

from tmis.workflow_automation.condition_engine.schemas import Condition
from tmis.workflow_automation.trigger_engine.schemas import TriggerType


def new_template_id() -> str:
    return f"tpl-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class TemplateTriggerSpec:
    trigger_type: TriggerType
    config: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TemplateStepSpec:
    order: int
    name: str
    action_type: str
    action_config: dict[str, str] = field(default_factory=dict)
    condition: Condition | None = None
    parallel_group: str | None = None


@dataclass(frozen=True, slots=True)
class WorkflowTemplate:
    """A reusable blueprint — "les modèles sont personnalisables"
    (sprint requirement): `instantiate()` accepts per-step config
    overrides without mutating the template itself."""

    id: str
    name: str
    case_type: str
    description: str = ""
    trigger_specs: tuple[TemplateTriggerSpec, ...] = field(default_factory=tuple)
    step_specs: tuple[TemplateStepSpec, ...] = field(default_factory=tuple)
    customizable: bool = True
