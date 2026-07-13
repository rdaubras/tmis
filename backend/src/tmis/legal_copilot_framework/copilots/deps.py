from dataclasses import dataclass

from tmis.ai.prompts.registry import PromptRegistry
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.legal_copilot_framework.document_packs.engine import DocumentPackEngine
from tmis.legal_copilot_framework.knowledge_packs.engine import KnowledgePackEngine
from tmis.legal_copilot_framework.prompt_packs.engine import PromptPackEngine
from tmis.legal_copilot_framework.reasoning_packs.engine import ReasoningPackEngine
from tmis.legal_copilot_framework.sdk.builder import CopilotBuilder
from tmis.legal_copilot_framework.validation_policies.engine import ValidationPolicyEngine
from tmis.legal_copilot_framework.workflow_packs.engine import WorkflowPackEngine
from tmis.workflow_automation.template_library.engine import TemplateLibrary


@dataclass(frozen=True, slots=True)
class DemoCopilotDeps:
    """Everything a demo copilot module needs to register its packs
    and build itself, bundled so each domain module's signature stays
    short. Every field is an existing sprint's engine or one of this
    sprint's own pack engines — never a new storage mechanism."""

    firm_id: str
    prompt_registry: PromptRegistry
    prompt_packs: PromptPackEngine
    knowledge_space: KnowledgeSpace
    knowledge_packs: KnowledgePackEngine
    reasoning_packs: ReasoningPackEngine
    document_packs: DocumentPackEngine
    workflow_packs: WorkflowPackEngine
    template_library: TemplateLibrary
    validation_policies: ValidationPolicyEngine
    builder: CopilotBuilder
