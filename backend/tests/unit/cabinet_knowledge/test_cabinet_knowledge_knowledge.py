import pytest

from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus, KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.platform.security.tenant_isolation import TenantAccessError

FIRM_A = "firm-a"
FIRM_B = "firm-b"


def _space() -> KnowledgeSpace:
    return KnowledgeSpace(InMemoryKnowledgeStore())


def test_create_starts_as_draft() -> None:
    obj = _space().create(FIRM_A, KnowledgeType.NOTE, "Note 1", {"text": "..."}, "avocat1")

    assert obj.status is KnowledgeStatus.DRAFT
    assert obj.version == 1
    assert obj.is_published is False


def test_get_returns_none_for_unknown_id() -> None:
    assert _space().get(FIRM_A, "does-not-exist") is None


def test_get_raises_on_cross_tenant_access() -> None:
    space = _space()
    obj = space.create(FIRM_A, KnowledgeType.NOTE, "Note", {}, "avocat1")

    with pytest.raises(TenantAccessError):
        space.get(FIRM_B, obj.id)


def test_list_is_scoped_to_firm() -> None:
    space = _space()
    space.create(FIRM_A, KnowledgeType.NOTE, "A", {}, "avocat1")
    space.create(FIRM_B, KnowledgeType.NOTE, "B", {}, "avocat2")

    assert [o.title for o in space.list(FIRM_A)] == ["A"]


def test_update_content_bumps_version_and_resets_to_draft() -> None:
    space = _space()
    obj = space.create(FIRM_A, KnowledgeType.NOTE, "Note", {"text": "v1"}, "avocat1")
    obj.status = KnowledgeStatus.VALIDATED
    obj.is_published = True

    updated = space.update_content(FIRM_A, obj.id, {"text": "v2"}, actor="avocat1")

    assert updated.version == 2
    assert updated.status is KnowledgeStatus.DRAFT
    assert updated.is_published is False


def test_add_tags_does_not_change_status_or_version() -> None:
    space = _space()
    obj = space.create(FIRM_A, KnowledgeType.NOTE, "Note", {}, "avocat1")

    updated = space.add_tags(FIRM_A, obj.id, frozenset({"rgpd"}))

    assert "rgpd" in updated.tags
    assert updated.version == 1
    assert updated.status is KnowledgeStatus.DRAFT


def test_record_usage_increments_counter() -> None:
    space = _space()
    obj = space.create(FIRM_A, KnowledgeType.NOTE, "Note", {}, "avocat1")

    space.record_usage(FIRM_A, obj.id)
    updated = space.record_usage(FIRM_A, obj.id)

    assert updated.usage_count == 2


def test_set_status_away_from_validated_unpublishes() -> None:
    space = _space()
    obj = space.create(FIRM_A, KnowledgeType.NOTE, "Note", {}, "avocat1")
    space.set_status(FIRM_A, obj.id, KnowledgeStatus.VALIDATED)
    obj.is_published = True

    updated = space.set_status(FIRM_A, obj.id, KnowledgeStatus.OBSOLETE)

    assert updated.is_published is False
