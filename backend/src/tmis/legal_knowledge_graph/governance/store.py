from tmis.legal_knowledge_graph.governance.schemas import NodeAccessPolicy


class InMemoryNodeAccessPolicyStore:
    def __init__(self) -> None:
        self._policies: dict[tuple[str, str], NodeAccessPolicy] = {}

    def save(self, policy: NodeAccessPolicy) -> None:
        self._policies[(policy.firm_id, policy.node_id)] = policy

    def get(self, firm_id: str, node_id: str) -> NodeAccessPolicy | None:
        return self._policies.get((firm_id, node_id))
