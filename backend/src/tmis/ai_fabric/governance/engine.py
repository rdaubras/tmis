from tmis.ai_fabric.governance.ports import GovernanceStorePort
from tmis.ai_fabric.governance.schemas import PolicyDecision, new_decision_id
from tmis.ai_fabric.policies.ports import PolicyStorePort
from tmis.ai_fabric.policies.schemas import PolicyType
from tmis.platform.licensing.engine import LicenseEngine

_ENTERPRISE_MODELS_FEATURE = "enterprise_ai_models"


class GovernanceEngine:
    """The sprint's "GOVERNANCE" policy engine — evaluated before the
    router is allowed to consider a model (see
    `tmis.ai_fabric.router`), and every decision is historized. Reuses
    `tmis.platform.licensing.LicenseEngine.has_feature` (Sprint 10)
    for the Enterprise-tier gate rather than inventing a second plan
    system."""

    def __init__(
        self,
        policy_store: PolicyStorePort,
        governance_store: GovernanceStorePort,
        license_engine: LicenseEngine,
    ) -> None:
        self._policy_store = policy_store
        self._governance_store = governance_store
        self._license_engine = license_engine

    def evaluate(
        self,
        firm_id: str,
        model_name: str,
        country: str | None = None,
        data_type: str | None = None,
        *,
        record: bool = True,
    ) -> PolicyDecision:
        reasons: list[str] = []
        allowed = True

        for policy in self._policy_store.list_for_model(model_name):
            if policy.type is PolicyType.MODEL_FORBIDDEN:
                allowed = False
                reasons.append(f"modèle interdit : {policy.reason}")
            elif policy.type is PolicyType.ENTERPRISE_ONLY:
                if not self._license_engine.has_feature(firm_id, _ENTERPRISE_MODELS_FEATURE):
                    allowed = False
                    reasons.append(f"réservé aux offres Enterprise : {policy.reason}")
            elif policy.type is PolicyType.COUNTRY_RESTRICTED:
                allowed_countries = policy.allowed_countries or frozenset()
                if country is None or country not in allowed_countries:
                    allowed = False
                    reasons.append(
                        f"pays non autorisé ({country!r}) : {policy.reason}"
                    )
            elif policy.type is PolicyType.DATA_TYPE_RESTRICTED:
                allowed_data_types = policy.allowed_data_types or frozenset()
                if data_type is None or data_type not in allowed_data_types:
                    allowed = False
                    reasons.append(
                        f"type de données non autorisé ({data_type!r}) : {policy.reason}"
                    )

        if not reasons:
            reasons.append("aucune politique restrictive applicable")

        decision = PolicyDecision(
            id=new_decision_id(),
            firm_id=firm_id,
            model_name=model_name,
            allowed=allowed,
            reasons=tuple(reasons),
        )
        if record:
            self._governance_store.append(decision)
        return decision

    def history(self, firm_id: str, model_name: str) -> list[PolicyDecision]:
        return self._governance_store.history(firm_id, model_name)
