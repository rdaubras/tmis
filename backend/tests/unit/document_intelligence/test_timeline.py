from tmis.document_intelligence.entities.regex_extractor import RegexEntityExtractor
from tmis.document_intelligence.timeline.builder import ChronologicalTimelineBuilder


def test_events_are_sorted_chronologically() -> None:
    text = (
        "Le contrat a été signé le 12 janvier 2019. Une modification est intervenue "
        "le 03/06/2021. Enfin, la résiliation a pris effet le 1 mars 2020."
    )
    entities = RegexEntityExtractor().extract(text)
    events = ChronologicalTimelineBuilder().build("doc-1", text, entities)

    assert [e.date for e in events] == ["12 janvier 2019", "1 mars 2020", "03/06/2021"]


def test_every_event_links_back_to_its_document() -> None:
    text = "Signé le 12 janvier 2019."
    entities = RegexEntityExtractor().extract(text)
    events = ChronologicalTimelineBuilder().build("doc-42", text, entities)

    assert all(event.document_id == "doc-42" for event in events)


def test_description_is_a_context_snippet_around_the_date() -> None:
    text = "Avant. " * 5 + "Signé le 12 janvier 2019." + " Après." * 5
    entities = RegexEntityExtractor().extract(text)
    events = ChronologicalTimelineBuilder().build("doc-1", text, entities)

    assert "12 janvier 2019" in events[0].description
    assert "\n" not in events[0].description


def test_ignores_non_date_entities() -> None:
    text = "Le loyer est de 1500 EUR, signé le 12 janvier 2019."
    entities = RegexEntityExtractor().extract(text)
    events = ChronologicalTimelineBuilder().build("doc-1", text, entities)

    assert len(events) == 1
    assert events[0].date == "12 janvier 2019"


def test_no_date_entities_returns_empty_timeline() -> None:
    events = ChronologicalTimelineBuilder().build("doc-1", "Aucune date ici.", [])
    assert events == []
