import pytest

from tmis.legal_drafting.templates.registry import TemplateRegistry
from tmis.legal_drafting.templates.schemas import (
    DocumentTemplate,
    DocumentType,
    SectionRole,
    TemplateSection,
)


def test_registry_has_all_nine_document_types() -> None:
    registry = TemplateRegistry()
    for document_type in DocumentType:
        template = registry.get_latest(document_type)
        assert template.document_type == document_type


def test_every_template_starts_with_header() -> None:
    registry = TemplateRegistry()
    for document_type in DocumentType:
        template = registry.get_latest(document_type)
        ordered = sorted(template.sections, key=lambda s: s.order)
        assert ordered[0].role == SectionRole.HEADER


def test_every_template_except_synthese_ends_with_signature() -> None:
    # `synthese` is an internal working document with no signature block.
    registry = TemplateRegistry()
    for document_type in DocumentType:
        if document_type == DocumentType.SYNTHESE:
            continue
        template = registry.get_latest(document_type)
        ordered = sorted(template.sections, key=lambda s: s.order)
        assert ordered[-1].role == SectionRole.SIGNATURE


def test_legal_discussion_depends_on_facts() -> None:
    registry = TemplateRegistry()
    template = registry.get_latest(DocumentType.CONSULTATION)
    facts_section = next(s for s in template.sections if s.role == SectionRole.FACTS)
    discussion_section = next(
        s for s in template.sections if s.role == SectionRole.LEGAL_DISCUSSION
    )
    assert facts_section.key in discussion_section.depends_on


def test_get_returns_none_for_unknown_id() -> None:
    registry = TemplateRegistry()
    assert registry.get("does-not-exist") is None


def test_get_returns_registered_template_by_id() -> None:
    registry = TemplateRegistry()
    template = registry.get_latest(DocumentType.COURRIER)
    assert registry.get(template.id) is template


def test_register_adds_a_new_version_without_removing_the_old_one() -> None:
    registry = TemplateRegistry()
    v1 = registry.get_latest(DocumentType.SYNTHESE)
    v2 = DocumentTemplate(
        id="synthese:v2",
        document_type=DocumentType.SYNTHESE,
        version=2,
        name="Synthese v2",
        sections=(
            TemplateSection(key="header", role=SectionRole.HEADER, title="En-tete", order=0),
        ),
    )
    registry.register(v2)

    versions = registry.list_versions(DocumentType.SYNTHESE)

    assert v1 in versions
    assert v2 in versions
    assert registry.get_latest(DocumentType.SYNTHESE) is v2


def test_get_latest_raises_for_unregistered_type() -> None:
    registry = TemplateRegistry()
    registry._by_type.clear()  # simulate an empty registry

    with pytest.raises(ValueError, match="No template"):
        registry.get_latest(DocumentType.MEMOIRE)
