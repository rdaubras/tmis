import dataclasses
import hashlib
import json
import time
import uuid
from typing import cast

from langgraph.graph.state import CompiledStateGraph

from tmis.ai.cache.factory import make_cache
from tmis.ai.cache.ports import CachePort
from tmis.ai.connectors.manager import ConnectorManager
from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.ai.embeddings.ports import EmbeddingProviderPort
from tmis.ai.evaluation.evaluator import Evaluator
from tmis.ai.evaluation.metrics import EvaluationMetrics, estimate_cost
from tmis.ai.events.bus import EventBus
from tmis.ai.events.events import Event, WorkflowFinished
from tmis.ai.guardrails.pipeline import GuardrailPipeline
from tmis.ai.kernel.config import KernelConfig, get_kernel_config
from tmis.ai.langgraph.graph import build_kernel_graph
from tmis.ai.langgraph.state import KernelWorkflowState
from tmis.ai.memory.case_memory import CaseMemory
from tmis.ai.memory.conversation_memory import ConversationMemory
from tmis.ai.memory.in_memory_store import InMemoryStore
from tmis.ai.memory.ports import MemoryStorePort
from tmis.ai.memory.user_memory import UserMemory
from tmis.ai.memory.workflow_memory import WorkflowMemory
from tmis.ai.prompts.registry import PromptRegistry
from tmis.ai.providers.registry import ProviderRegistry
from tmis.ai.rag.pipeline import RagPipeline
from tmis.ai.schemas.agent import AgentOutput, AgentPort
from tmis.ai.schemas.connector import ConnectorDocument
from tmis.ai.schemas.provider import ModelResponse
from tmis.ai.tools.registry import ToolRegistry

DEMO_WORKFLOW_NAME = "kernel_demo"


class TMISKernel:
    """Single entry point for every AI capability in TMIS.

    Responsibilities (see docs/10-ai-kernel.md): initializing AI
    components, registering agents and workflows, mediating every model
    provider and connector call, and owning memory/cache/events/prompts/
    configuration. No agent is allowed to call a provider or connector
    directly — they call `TMISKernel.complete()` / `search_connectors()`.
    """

    def __init__(
        self,
        config: KernelConfig | None = None,
        *,
        provider_registry: ProviderRegistry | None = None,
        connector_manager: ConnectorManager | None = None,
        cache: CachePort | None = None,
        memory_store: MemoryStorePort | None = None,
        event_bus: EventBus | None = None,
        prompt_registry: PromptRegistry | None = None,
        tool_registry: ToolRegistry | None = None,
        guardrails: GuardrailPipeline | None = None,
        evaluator: Evaluator | None = None,
        embedding_provider: EmbeddingProviderPort | None = None,
        rag: RagPipeline | None = None,
    ) -> None:
        self.config = config or get_kernel_config()

        self.provider_registry = provider_registry or ProviderRegistry()
        self.connector_manager = connector_manager or ConnectorManager()
        self.cache: CachePort = cache or make_cache()
        self.event_bus = event_bus or EventBus()
        self.prompt_registry = prompt_registry or PromptRegistry()
        self.tool_registry = tool_registry or ToolRegistry()
        self.guardrails = guardrails or GuardrailPipeline()
        self.evaluator = evaluator or Evaluator()
        self.embedding_provider = embedding_provider or HashingEmbeddingProvider()
        self.rag = rag or RagPipeline(embedding_provider=self.embedding_provider)

        store = memory_store or InMemoryStore()
        self.conversation_memory = ConversationMemory(store)
        self.case_memory = CaseMemory(store)
        self.workflow_memory = WorkflowMemory(store)
        self.user_memory = UserMemory(store)

        self._agents: dict[str, AgentPort] = {}
        self._workflows: dict[str, CompiledStateGraph] = {}
        self.register_workflow(DEMO_WORKFLOW_NAME, build_kernel_graph(self))

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register_agent(self, name: str, agent: AgentPort) -> None:
        self._agents[name] = agent

    def get_agent(self, name: str) -> AgentPort:
        try:
            return self._agents[name]
        except KeyError as exc:
            raise ValueError(f"Unknown agent: {name!r}") from exc

    def list_agents(self) -> list[str]:
        return list(self._agents)

    def register_workflow(self, name: str, graph: CompiledStateGraph) -> None:
        self._workflows[name] = graph

    def get_workflow(self, name: str) -> CompiledStateGraph:
        try:
            return self._workflows[name]
        except KeyError as exc:
            raise ValueError(f"Unknown workflow: {name!r}") from exc

    def list_workflows(self) -> list[str]:
        return list(self._workflows)

    # ------------------------------------------------------------------
    # The single gateway to model providers
    # ------------------------------------------------------------------
    async def complete(
        self, prompt: str, *, provider: str | None = None, use_cache: bool = True
    ) -> ModelResponse:
        self.guardrails.validate_input(prompt)
        provider_name = provider or self.config.default_provider
        cache_key = (
            f"complete:{provider_name}:{hashlib.sha256(prompt.encode()).hexdigest()}"
        )

        if use_cache and self.config.use_cache:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return ModelResponse(**json.loads(cached))

        provider_impl = self.provider_registry.get(provider_name)
        start = time.perf_counter()
        response = await provider_impl.complete(prompt)
        latency_ms = (time.perf_counter() - start) * 1000

        if use_cache and self.config.use_cache:
            await self.cache.set(
                cache_key,
                json.dumps(dataclasses.asdict(response)),
                ttl_seconds=self.config.cache_ttl_seconds,
            )

        self.evaluator.record(
            EvaluationMetrics(
                provider=response.provider,
                model=response.model,
                latency_ms=latency_ms,
                token_count=response.total_tokens,
                estimated_cost_usd=estimate_cost(response.provider, response.total_tokens),
                confidence_score=1.0,
            )
        )
        return response

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self.embedding_provider.embed(texts)

    # ------------------------------------------------------------------
    # The single gateway to document connectors
    # ------------------------------------------------------------------
    async def search_connectors(
        self,
        query: str,
        *,
        connector_names: list[str] | None = None,
        filters: dict[str, object] | None = None,
        use_cache: bool = True,
    ) -> list[ConnectorDocument]:
        targets = connector_names or self.config.default_connectors
        query_hash = hashlib.sha256(query.encode()).hexdigest()
        cache_key = f"search:{','.join(sorted(targets))}:{query_hash}"

        if use_cache and self.config.use_cache:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return [ConnectorDocument(**doc) for doc in json.loads(cached)]

        results = await self.connector_manager.search(
            query, filters=filters, connector_names=targets
        )

        if use_cache and self.config.use_cache:
            await self.cache.set(
                cache_key,
                json.dumps([dataclasses.asdict(doc) for doc in results]),
                ttl_seconds=self.config.cache_ttl_seconds,
            )
        return results

    # ------------------------------------------------------------------
    # Guardrails, prompts, tools, events — thin pass-throughs so callers
    # only ever depend on the Kernel.
    # ------------------------------------------------------------------
    def validate_output(self, output: AgentOutput) -> list[str]:
        return self.guardrails.validate_output(output)

    def get_prompt(self, prompt_id: str, *, version: int | None = None, **variables: str) -> str:
        return self.prompt_registry.render(prompt_id, version=version, **variables)

    async def run_tool(self, name: str, **kwargs: object) -> object:
        return await self.tool_registry.run(name, **kwargs)

    async def publish_event(self, event: Event) -> None:
        await self.event_bus.publish(event)

    # ------------------------------------------------------------------
    # Workflow execution
    # ------------------------------------------------------------------
    async def run_workflow(
        self, name: str, question: str, *, workflow_id: uuid.UUID | None = None
    ) -> KernelWorkflowState:
        workflow_id = workflow_id or uuid.uuid4()
        graph = self.get_workflow(name)
        initial_state: KernelWorkflowState = {
            "workflow_id": workflow_id,
            "question": question,
            "analysis": None,
            "research": [],
            "verification_warnings": [],
            "response": None,
        }
        final_state = await graph.ainvoke(initial_state)
        await self.workflow_memory.record_step(workflow_id, f"workflow_finished:{name}")
        await self.publish_event(
            WorkflowFinished(workflow_id=workflow_id, workflow_name=name, success=True)
        )
        return cast(KernelWorkflowState, final_state)
