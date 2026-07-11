from tmis.ai_governance.reasoning_chain.schemas import ReasoningChain


class InMemoryReasoningChainStore:
    def __init__(self) -> None:
        self._chains: dict[tuple[str, str], ReasoningChain] = {}

    def save(self, chain: ReasoningChain) -> None:
        self._chains[(chain.firm_id, chain.production_id)] = chain

    def get(self, firm_id: str, production_id: str) -> ReasoningChain | None:
        return self._chains.get((firm_id, production_id))
