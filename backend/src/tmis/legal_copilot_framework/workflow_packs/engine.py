from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.legal_copilot_framework.workflow_packs.ports import WorkflowPackStorePort
from tmis.legal_copilot_framework.workflow_packs.schemas import WorkflowPack
from tmis.workflow_automation.template_library.engine import TemplateLibrary
from tmis.workflow_automation.workflow_engine.schemas import Workflow


class WorkflowPackEngine:
    """Composes `workflow_automation.template_library.TemplateLibrary`
    (Sprint 17) — never a second Workflow Engine. `instantiate_pack`
    always goes through `TemplateLibrary.instantiate`, so every
    produced `Workflow` is a normal, versioned workflow, exactly as
    if a cabinet had instantiated one of the six built-in templates."""

    def __init__(self, store: WorkflowPackStorePort, template_library: TemplateLibrary) -> None:
        self._store = store
        self._template_library = template_library

    def register_pack(
        self,
        pack_id: str,
        name: str,
        domain: LegalDomain,
        *,
        workflow_template_ids: tuple[str, ...] = (),
    ) -> WorkflowPack:
        existing = self._store.history(pack_id)
        version = existing[-1].version + 1 if existing else 1
        pack = WorkflowPack(
            id=pack_id,
            name=name,
            domain=domain,
            version=version,
            workflow_template_ids=workflow_template_ids,
        )
        self._store.save(pack)
        return pack

    def get(self, pack_id: str, version: int | None = None) -> WorkflowPack:
        pack = self._store.get(pack_id, version)
        if pack is None:
            raise KeyError(pack_id)
        return pack

    def instantiate_pack(self, firm_id: str, owner: str, pack_id: str) -> list[Workflow]:
        pack = self.get(pack_id)
        return [
            self._template_library.instantiate(template_id, firm_id, owner)
            for template_id in pack.workflow_template_ids
        ]
