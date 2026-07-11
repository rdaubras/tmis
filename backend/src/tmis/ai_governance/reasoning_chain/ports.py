from typing import Protocol

from tmis.ai_governance.reasoning_chain.schemas import ReasoningChain


class ReasoningChainStorePort(Protocol):
    def save(self, chain: ReasoningChain) -> None: ...

    def get(self, firm_id: str, production_id: str) -> ReasoningChain | None: ...
