"""First LangGraph orchestration owned by the AI Kernel.

Utilisateur -> Orchestrateur -> Analyse -> Recherche -> Vérification ->
Réponse (see docs/11-langgraph-architecture.md). Nodes depend only on
`KernelFacadePort` (see `ports.py`), never on the concrete `TMISKernel`
class, so there is no circular import between `tmis.ai.kernel` and
`tmis.ai.langgraph`.
"""
