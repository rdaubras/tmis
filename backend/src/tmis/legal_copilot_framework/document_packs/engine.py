from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.cabinet_knowledge.templates.engine import CabinetTemplateEngine
from tmis.cabinet_knowledge.templates.schemas import CabinetTemplate
from tmis.legal_copilot_framework.document_packs.ports import DocumentPackStorePort
from tmis.legal_copilot_framework.document_packs.schemas import DocumentPack
from tmis.legal_drafting.templates.registry import TemplateRegistry
from tmis.legal_drafting.templates.schemas import DocumentTemplate, DocumentType


class DocumentPackEngine:
    """Composes `legal_drafting.templates.TemplateRegistry` (Sprint 7)
    and `cabinet_knowledge.templates.CabinetTemplateEngine` (Sprint
    12) — never a third document-structure schema."""

    def __init__(
        self,
        store: DocumentPackStorePort,
        template_registry: TemplateRegistry,
        cabinet_template_engine: CabinetTemplateEngine,
    ) -> None:
        self._store = store
        self._template_registry = template_registry
        self._cabinet_template_engine = cabinet_template_engine

    def register_pack(
        self,
        pack_id: str,
        name: str,
        domain: LegalDomain,
        *,
        document_types: tuple[DocumentType, ...] = (),
        cabinet_template_ids: tuple[str, ...] = (),
        validations: tuple[str, ...] = (),
        quality_controls: tuple[str, ...] = (),
    ) -> DocumentPack:
        existing = self._store.history(pack_id)
        version = existing[-1].version + 1 if existing else 1
        pack = DocumentPack(
            id=pack_id,
            name=name,
            domain=domain,
            version=version,
            document_types=document_types,
            cabinet_template_ids=cabinet_template_ids,
            validations=validations,
            quality_controls=quality_controls,
        )
        self._store.save(pack)
        return pack

    def get(self, pack_id: str, version: int | None = None) -> DocumentPack:
        pack = self._store.get(pack_id, version)
        if pack is None:
            raise KeyError(pack_id)
        return pack

    def resolve_document_templates(self, pack_id: str) -> list[DocumentTemplate]:
        pack = self.get(pack_id)
        return [
            self._template_registry.get_latest(document_type)
            for document_type in pack.document_types
        ]

    def resolve_cabinet_templates(self, firm_id: str, pack_id: str) -> list[CabinetTemplate]:
        pack = self.get(pack_id)
        templates = []
        for template_id in pack.cabinet_template_ids:
            try:
                templates.append(self._cabinet_template_engine.get_template(firm_id, template_id))
            except KeyError:
                continue
        return templates
