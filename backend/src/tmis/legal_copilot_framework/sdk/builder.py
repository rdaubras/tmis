from collections.abc import Callable

from tmis.ai_team.teams.engine import TeamBuilder
from tmis.legal_copilot_framework.copilot.engine import CopilotEngine
from tmis.legal_copilot_framework.copilot.schemas import CopilotStatus, LegalCopilot
from tmis.legal_copilot_framework.document_packs.engine import DocumentPackEngine
from tmis.legal_copilot_framework.knowledge_packs.engine import KnowledgePackEngine
from tmis.legal_copilot_framework.prompt_packs.engine import PromptPackEngine
from tmis.legal_copilot_framework.reasoning_packs.engine import ReasoningPackEngine
from tmis.legal_copilot_framework.registry.engine import CopilotRegistry
from tmis.legal_copilot_framework.registry.schemas import CopilotManifest
from tmis.legal_copilot_framework.sdk.schemas import CopilotSpec
from tmis.legal_copilot_framework.validation_policies.engine import ValidationPolicyEngine
from tmis.legal_copilot_framework.workflow_packs.engine import WorkflowPackEngine


class CopilotValidationError(ValueError):
    """Raised when a `CopilotSpec` references a pack, agent role, or
    policy id that does not resolve — never installed partially."""


class CopilotBuilder:
    """The Copilot SDK's entry point: turns a `CopilotSpec` into a
    registered `LegalCopilot`, composing `ai_team.teams.TeamBuilder`
    (Sprint 11) for the agent team and every pack engine of this
    sprint for validation. Adding a new copilot never requires
    changing this class — only calling `build()` with a new spec."""

    def __init__(
        self,
        team_builder: TeamBuilder,
        copilot_engine: CopilotEngine,
        registry: CopilotRegistry,
        prompt_packs: PromptPackEngine,
        knowledge_packs: KnowledgePackEngine,
        reasoning_packs: ReasoningPackEngine,
        document_packs: DocumentPackEngine,
        workflow_packs: WorkflowPackEngine,
        validation_policies: ValidationPolicyEngine,
    ) -> None:
        self._team_builder = team_builder
        self._copilot_engine = copilot_engine
        self._registry = registry
        self._prompt_packs = prompt_packs
        self._knowledge_packs = knowledge_packs
        self._reasoning_packs = reasoning_packs
        self._document_packs = document_packs
        self._workflow_packs = workflow_packs
        self._validation_policies = validation_policies

    def build(self, spec: CopilotSpec) -> LegalCopilot:
        self._validate(spec)
        team = self._team_builder.build_custom_team(spec.name, list(spec.agent_ids))

        copilot = LegalCopilot(
            id=spec.id,
            name=spec.name,
            domain=spec.domain,
            description=spec.description,
            version=spec.version,
            dependencies=spec.dependencies,
            team_id=team.id,
            compatible_models=spec.compatible_models,
            prompt_pack_id=spec.prompt_pack_id,
            knowledge_pack_ids=spec.knowledge_pack_ids,
            reasoning_pack_ids=spec.reasoning_pack_ids,
            document_pack_ids=spec.document_pack_ids,
            workflow_pack_ids=spec.workflow_pack_ids,
            validation_policy_ids=spec.validation_policy_ids,
            permissions=spec.permissions,
            metrics_enabled=spec.metrics_enabled,
        )
        self._copilot_engine.define(copilot)
        self._registry.register(
            CopilotManifest(
                copilot_id=spec.id,
                version=spec.version,
                domain=spec.domain,
                author=spec.author,
                status=CopilotStatus.DRAFT,
                dependencies=spec.dependencies,
                compatibility=spec.compatibility,
            )
        )
        return copilot

    def _validate(self, spec: CopilotSpec) -> None:
        errors: list[str] = []

        if spec.prompt_pack_id is not None:
            self._check(errors, "prompt pack", spec.prompt_pack_id, self._prompt_packs.get)
        for pack_id in spec.knowledge_pack_ids:
            self._check(errors, "knowledge pack", pack_id, self._knowledge_packs.get)
        for pack_id in spec.reasoning_pack_ids:
            self._check(errors, "reasoning pack", pack_id, self._reasoning_packs.get)
        for pack_id in spec.document_pack_ids:
            self._check(errors, "document pack", pack_id, self._document_packs.get)
        for pack_id in spec.workflow_pack_ids:
            self._check(errors, "workflow pack", pack_id, self._workflow_packs.get)
        for policy_id in spec.validation_policy_ids:
            self._check(errors, "validation policy", policy_id, self._validation_policies.get)

        if errors:
            raise CopilotValidationError("; ".join(errors))

    @staticmethod
    def _check(
        errors: list[str], kind: str, ref_id: str, resolver: Callable[[str], object]
    ) -> None:
        try:
            resolver(ref_id)
        except KeyError:
            errors.append(f"{kind} not found: {ref_id}")
