from tmis.case_intelligence.actors.schemas import Actor, ActorType, CaseActorRole
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.schemas import CaseProfile


def test_get_or_create_creates_a_new_profile() -> None:
    store = InMemoryCaseStore()
    profile = store.get_or_create("case-1", "Dupont c. ACME")
    assert profile.case_id == "case-1"
    assert profile.title == "Dupont c. ACME"


def test_get_or_create_returns_existing_profile_unchanged() -> None:
    store = InMemoryCaseStore()
    first = store.get_or_create("case-1", "Dupont c. ACME")
    first.title = "Renamed"
    second = store.get_or_create("case-1", "Different title")
    assert second is first
    assert second.title == "Renamed"


def test_get_missing_profile_returns_none() -> None:
    assert InMemoryCaseStore().get("missing") is None


def test_save_then_get_roundtrips() -> None:
    store = InMemoryCaseStore()
    profile = CaseProfile(case_id="case-1", title="Test")
    store.save(profile)
    assert store.get("case-1") is profile


def test_list_ids_returns_every_saved_case() -> None:
    store = InMemoryCaseStore()
    store.save(CaseProfile(case_id="case-1", title="A"))
    store.save(CaseProfile(case_id="case-2", title="B"))
    assert set(store.list_ids()) == {"case-1", "case-2"}


def test_actor_role_properties_filter_correctly() -> None:
    client = Actor(id="a1", type=ActorType.PERSON, name="Client")
    opposing = Actor(id="a2", type=ActorType.COMPANY, name="Opposing")
    profile = CaseProfile(case_id="case-1", title="Test", actors=[client, opposing])
    profile.actor_roles = {"a1": CaseActorRole.CLIENT, "a2": CaseActorRole.OPPOSING_PARTY}

    assert profile.clients == [client]
    assert profile.opposing_parties == [opposing]
    assert profile.lawyers == []


def test_record_ai_action_appends_a_timestamped_entry() -> None:
    profile = CaseProfile(case_id="case-1", title="Test")
    profile.record_ai_action("Document doc-1 traité.")
    assert len(profile.ai_history) == 1
    assert "Document doc-1 traité." in profile.ai_history[0]
