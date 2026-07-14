from datetime import UTC, datetime

from tmis.identity_platform.abac.schemas import AbacAttributes
from tmis.legal_knowledge_graph.governance.ports import NodeAccessPolicyStorePort
from tmis.legal_knowledge_graph.governance.schemas import NodeAccessPolicy, new_access_policy_id

_DEFAULT_CONFIDENTIALITY = "standard"


class GraphAccessPolicyEngine:
    """Owns retention/confidentiality metadata per node — the actual
    "qui peut voir/modifier/publier" decision is always taken by
    `identity_platform.api.guard.authorize_or_403` (RBAC + ABAC +
    Zero Trust, Sprint 19) using `Permission.KNOWLEDGE_GRAPH_MANAGE`
    and the `AbacAttributes` this engine hands back — never a second
    authorization mechanism."""

    def __init__(self, store: NodeAccessPolicyStorePort) -> None:
        self._store = store

    def set_policy(
        self,
        firm_id: str,
        node_id: str,
        *,
        confidentiality_level: str = _DEFAULT_CONFIDENTIALITY,
        retention_days: int | None = None,
    ) -> NodeAccessPolicy:
        policy = NodeAccessPolicy(
            id=new_access_policy_id(),
            firm_id=firm_id,
            node_id=node_id,
            confidentiality_level=confidentiality_level,
            retention_days=retention_days,
        )
        self._store.save(policy)
        return policy

    def get_policy(self, firm_id: str, node_id: str) -> NodeAccessPolicy | None:
        return self._store.get(firm_id, node_id)

    def abac_attributes_for(self, firm_id: str, node_id: str) -> AbacAttributes:
        policy = self.get_policy(firm_id, node_id)
        level = policy.confidentiality_level if policy else _DEFAULT_CONFIDENTIALITY
        return AbacAttributes(confidentiality_level=level)

    def is_past_retention(self, firm_id: str, node_id: str, as_of: datetime | None = None) -> bool:
        policy = self.get_policy(firm_id, node_id)
        if policy is None or policy.retention_days is None:
            return False
        reference = as_of or datetime.now(UTC)
        return (reference - policy.created_at).days > policy.retention_days
