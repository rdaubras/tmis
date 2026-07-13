import pytest

from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.templates.engine import CabinetTemplateEngine
from tmis.legal_copilot_framework.document_packs.engine import DocumentPackEngine
from tmis.legal_copilot_framework.document_packs.store import InMemoryDocumentPackStore
from tmis.legal_drafting.templates.registry import TemplateRegistry
from tmis.legal_drafting.templates.schemas import DocumentType

FIRM = "firm-a"


def _engine() -> tuple[DocumentPackEngine, TemplateRegistry, CabinetTemplateEngine]:
    space = KnowledgeSpace(InMemoryKnowledgeStore())
    registry = TemplateRegistry()
    cabinet_templates = CabinetTemplateEngine(space)
    engine = DocumentPackEngine(InMemoryDocumentPackStore(), registry, cabinet_templates)
    return engine, registry, cabinet_templates


def test_register_pack_versions_increment() -> None:
    engine, _, _ = _engine()
    first = engine.register_pack("dp-1", "Pack", LegalDomain.CIVIL)
    second = engine.register_pack("dp-1", "Pack", LegalDomain.CIVIL)

    assert first.version == 1
    assert second.version == 2


def test_get_unknown_pack_raises_key_error() -> None:
    engine, _, _ = _engine()
    with pytest.raises(KeyError):
        engine.get("missing")


def test_resolve_document_templates_returns_matching_structural_templates() -> None:
    engine, _, _ = _engine()
    engine.register_pack(
        "dp-1", "Pack", LegalDomain.CIVIL, document_types=(DocumentType.ASSIGNATION,)
    )

    templates = engine.resolve_document_templates("dp-1")

    assert len(templates) == 1
    assert templates[0].document_type is DocumentType.ASSIGNATION


def test_resolve_cabinet_templates_returns_matching_cabinet_customizations() -> None:
    engine, _, cabinet_templates = _engine()
    cabinet_template = cabinet_templates.create_template(
        FIRM, "Modèle maison", DocumentType.COURRIER, ("header", "body"), "author"
    )
    engine.register_pack(
        "dp-1", "Pack", LegalDomain.CIVIL, cabinet_template_ids=(cabinet_template.id,)
    )

    resolved = engine.resolve_cabinet_templates(FIRM, "dp-1")

    assert [t.id for t in resolved] == [cabinet_template.id]


def test_resolve_cabinet_templates_skips_unresolvable_ids() -> None:
    engine, _, _ = _engine()
    engine.register_pack("dp-1", "Pack", LegalDomain.CIVIL, cabinet_template_ids=("unknown",))

    assert engine.resolve_cabinet_templates(FIRM, "dp-1") == []
