import pytest

from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.versioning.service import InMemoryVersioningService


def _section(text: str = "Texte initial.") -> list[Section]:
    paragraph = Paragraph(id="p1", section_key="facts", order=0, text=text, origin="kernel")
    return [Section(id="s1", key="facts", title="Faits", order=0, paragraphs=[paragraph])]


def test_snapshot_creates_incrementing_version_numbers() -> None:
    service = InMemoryVersioningService()
    v1 = service.snapshot("doc1", _section(), "system")
    v2 = service.snapshot("doc1", _section(), "system")
    assert v1.version_number == 1
    assert v2.version_number == 2


def test_snapshot_is_a_deep_copy_immune_to_later_mutation() -> None:
    service = InMemoryVersioningService()
    sections = _section()
    version = service.snapshot("doc1", sections, "system")

    sections[0].paragraphs[0].text = "Texte modifié."

    assert version.sections[0].paragraphs[0].text == "Texte initial."


def test_get_returns_none_for_unknown_version() -> None:
    service = InMemoryVersioningService()
    assert service.get("doc1", 99) is None


def test_compare_detects_added_removed_and_changed_paragraphs() -> None:
    service = InMemoryVersioningService()
    service.snapshot("doc1", _section(), "system")

    changed_sections = _section()
    changed_sections[0].paragraphs[0].text = "Texte modifié."
    changed_sections[0].paragraphs.append(
        Paragraph(id="p2", section_key="facts", order=1, text="Nouveau.", origin="kernel")
    )
    service.snapshot("doc1", changed_sections, "system")

    diff = service.compare("doc1", 1, 2)

    assert diff.changed_paragraph_ids == ("p1",)
    assert diff.added_paragraph_ids == ("p2",)
    assert diff.removed_paragraph_ids == ()


def test_compare_raises_for_unknown_version() -> None:
    service = InMemoryVersioningService()
    service.snapshot("doc1", _section(), "system")
    with pytest.raises(ValueError, match="Unknown version"):
        service.compare("doc1", 1, 99)


def test_restore_returns_a_copy_of_the_requested_version() -> None:
    service = InMemoryVersioningService()
    service.snapshot("doc1", _section(), "system")
    service.snapshot("doc1", _section("Texte v2."), "system")

    restored = service.restore("doc1", 1)

    assert restored[0].paragraphs[0].text == "Texte initial."
