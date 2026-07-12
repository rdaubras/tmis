from functools import lru_cache

from tmis.ai_governance.bootstrap import get_human_validation_engine
from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.collaboration.bootstrap import get_notification_engine
from tmis.collaboration.notifications.engine import NotificationEngine
from tmis.workflow_automation.action_engine.engine import ActionEngine
from tmis.workflow_automation.action_engine.store import InMemoryActionLogStore
from tmis.workflow_automation.approval_gateway.engine import ApprovalGatewayEngine
from tmis.workflow_automation.approval_gateway.store import InMemoryApprovalPolicyStore
from tmis.workflow_automation.audit.engine import WorkflowAuditEngine
from tmis.workflow_automation.audit.store import InMemoryWorkflowAuditStore
from tmis.workflow_automation.condition_engine.engine import ConditionEngine
from tmis.workflow_automation.event_bus.bus import WorkflowEventBus
from tmis.workflow_automation.execution_engine.engine import ExecutionEngine
from tmis.workflow_automation.execution_engine.store import InMemoryExecutionStore
from tmis.workflow_automation.integrations.registry import IntegrationRegistry
from tmis.workflow_automation.metrics.engine import WorkflowMetricsEngine
from tmis.workflow_automation.metrics.sinks import InMemoryWorkflowMetricsSink
from tmis.workflow_automation.notifications.adapter import WorkflowNotificationAdapter
from tmis.workflow_automation.retry.engine import WorkflowRetryPolicy
from tmis.workflow_automation.rollback.engine import RollbackEngine
from tmis.workflow_automation.rollback.store import InMemoryRollbackLogStore
from tmis.workflow_automation.rule_engine.engine import RuleEngine
from tmis.workflow_automation.rule_engine.store import InMemoryRuleStore
from tmis.workflow_automation.scheduler.engine import SchedulerEngine
from tmis.workflow_automation.scheduler.store import InMemorySchedulerStore
from tmis.workflow_automation.simulation.engine import SimulationEngine
from tmis.workflow_automation.template_library.defaults import build_default_templates
from tmis.workflow_automation.template_library.engine import TemplateLibrary
from tmis.workflow_automation.trigger_engine.engine import TriggerEngine
from tmis.workflow_automation.workflow_engine.engine import WorkflowEngine
from tmis.workflow_automation.workflow_engine.store import InMemoryWorkflowStore


@lru_cache
def get_workflow_event_bus() -> WorkflowEventBus:
    """Process-wide composition root for `tmis.workflow_automation`
    (see docs/92-architecture-workflow-automation.md)."""
    return WorkflowEventBus()


@lru_cache
def get_trigger_engine() -> TriggerEngine:
    return TriggerEngine()


@lru_cache
def get_condition_engine() -> ConditionEngine:
    return ConditionEngine()


@lru_cache
def get_rule_engine() -> RuleEngine:
    return RuleEngine(InMemoryRuleStore(), get_condition_engine())


@lru_cache
def get_action_engine() -> ActionEngine:
    return ActionEngine(InMemoryActionLogStore())


@lru_cache
def get_approval_gateway_engine() -> ApprovalGatewayEngine:
    human_validation_engine: HumanValidationEngine = get_human_validation_engine()
    return ApprovalGatewayEngine(human_validation_engine, InMemoryApprovalPolicyStore())


@lru_cache
def get_workflow_engine() -> WorkflowEngine:
    return WorkflowEngine(InMemoryWorkflowStore())


@lru_cache
def get_scheduler_engine() -> SchedulerEngine:
    return SchedulerEngine(InMemorySchedulerStore())


@lru_cache
def get_retry_policy() -> WorkflowRetryPolicy:
    return WorkflowRetryPolicy()


@lru_cache
def get_execution_engine() -> ExecutionEngine:
    return ExecutionEngine(
        InMemoryExecutionStore(), get_action_engine(), get_condition_engine(), get_retry_policy()
    )


@lru_cache
def get_rollback_engine() -> RollbackEngine:
    return RollbackEngine(InMemoryRollbackLogStore())


@lru_cache
def get_simulation_engine() -> SimulationEngine:
    return SimulationEngine(get_condition_engine())


@lru_cache
def get_template_library() -> TemplateLibrary:
    library = TemplateLibrary(get_workflow_engine())
    for template in build_default_templates():
        library.register(template)
    return library


@lru_cache
def get_workflow_notification_adapter() -> WorkflowNotificationAdapter:
    notification_engine: NotificationEngine = get_notification_engine()
    return WorkflowNotificationAdapter(notification_engine)


@lru_cache
def get_integration_registry() -> IntegrationRegistry:
    return IntegrationRegistry()


@lru_cache
def get_workflow_audit_engine() -> WorkflowAuditEngine:
    return WorkflowAuditEngine(InMemoryWorkflowAuditStore())


@lru_cache
def get_workflow_metrics_sink() -> InMemoryWorkflowMetricsSink:
    return InMemoryWorkflowMetricsSink()


@lru_cache
def get_workflow_metrics_engine() -> WorkflowMetricsEngine:
    return WorkflowMetricsEngine([get_workflow_metrics_sink()])
