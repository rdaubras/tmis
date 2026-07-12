from datetime import UTC, datetime

from tmis.business_platform.modules.ports import ModuleActivationStorePort
from tmis.business_platform.modules.schemas import ModuleActivation, TmisModule
from tmis.business_platform.plans.engine import PlanCatalog
from tmis.business_platform.subscriptions.engine import SubscriptionEngine


class ModuleNotAvailableError(RuntimeError):
    """Raised when activating a module the firm's plan does not
    include as a feature — an explicit override cannot grant a
    module the plan itself does not offer; that requires a plan
    change, not a toggle."""


_MODULE_FEATURE_MAPPING: dict[TmisModule, str] = {
    TmisModule.DOCUMENT_INTELLIGENCE: "documents",
    TmisModule.CASE_INTELLIGENCE: "cases",
    TmisModule.LEGAL_RESEARCH: "ai_assist",
    TmisModule.LEGAL_REASONING: "ai_assist",
    TmisModule.LEGAL_DRAFTING: "ai_assist",
    TmisModule.AI_TEAM: "ai_assist",
    TmisModule.AI_FABRIC: "ai_assist",
    TmisModule.AI_GOVERNANCE: "ai_assist",
    TmisModule.COLLABORATION: "collaboration",
    TmisModule.WORKFLOW_AUTOMATION: "workflow_automation",
    TmisModule.INTEGRATION_HUB: "integration_hub",
    TmisModule.STRATEGIC_INTELLIGENCE: "advanced_analytics",
    TmisModule.PLATFORM_SDK: "public_api",
}
"""Maps a bounded context to the `Plan.features` string that gates
it commercially (see `plans.engine._DEFAULT_FEATURES`). A module
absent from this mapping (`cabinet_os`, `cabinet_knowledge`,
`identity_platform`) is foundational — available on every plan,
never commercially gated."""


class ModuleRegistry:
    """Per-firm activation state for the TMIS bounded contexts. A
    module defaults to available when its value appears in the
    firm's current plan `features`; `ModuleActivation` records let a
    firm explicitly turn an available module off (or back on)
    without changing the plan-derived default for other firms."""

    def __init__(
        self,
        store: ModuleActivationStorePort,
        plans: PlanCatalog,
        subscriptions: SubscriptionEngine,
    ) -> None:
        self._store = store
        self._plans = plans
        self._subscriptions = subscriptions

    def is_available(self, firm_id: str, module: TmisModule) -> bool:
        feature = _MODULE_FEATURE_MAPPING.get(module)
        if feature is None:
            return True
        subscription = self._subscriptions.get(firm_id)
        plan = self._plans.get(subscription.plan_id)
        return feature in plan.features

    def activate(self, firm_id: str, module: TmisModule) -> ModuleActivation:
        if not self.is_available(firm_id, module):
            raise ModuleNotAvailableError(
                f"{module.value} is not included in firm {firm_id}'s plan"
            )
        activation = ModuleActivation(
            firm_id=firm_id, module=module, active=True, updated_at=datetime.now(UTC)
        )
        self._store.save(activation)
        return activation

    def deactivate(self, firm_id: str, module: TmisModule) -> ModuleActivation:
        activation = ModuleActivation(
            firm_id=firm_id, module=module, active=False, updated_at=datetime.now(UTC)
        )
        self._store.save(activation)
        return activation

    def is_active(self, firm_id: str, module: TmisModule) -> bool:
        override = self._store.get(firm_id, module)
        if override is not None:
            return override.active
        return self.is_available(firm_id, module)

    def active_modules(self, firm_id: str) -> list[TmisModule]:
        return [module for module in TmisModule if self.is_active(firm_id, module)]
