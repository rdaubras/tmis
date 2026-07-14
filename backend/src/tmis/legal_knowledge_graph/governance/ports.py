from typing import Protocol

from tmis.legal_knowledge_graph.governance.schemas import NodeAccessPolicy


class NodeAccessPolicyStorePort(Protocol):
    def save(self, policy: NodeAccessPolicy) -> None: ...

    def get(self, firm_id: str, node_id: str) -> NodeAccessPolicy | None: ...
