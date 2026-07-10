from tmis.document_intelligence.entities.regex_extractor import RegexEntityExtractor
from tmis.document_intelligence.schemas.entities import EntityType


def _values(text: str, entity_type: EntityType) -> list[str]:
    entities = RegexEntityExtractor().extract(text)
    return [e.value for e in entities if e.type == entity_type]


def test_extracts_french_date() -> None:
    assert "12 janvier 2019" in _values("Signé le 12 janvier 2019.", EntityType.DATE)


def test_extracts_numeric_date() -> None:
    assert "03/06/2021" in _values("Modification le 03/06/2021.", EntityType.DATE)


def test_extracts_amount() -> None:
    assert any("EUR" in v for v in _values("Le loyer est de 1 500 EUR.", EntityType.AMOUNT))


def test_extracts_law_article() -> None:
    assert "article 1240" in _values("Voir article 1240 du code civil.", EntityType.LAW_ARTICLE)


def test_extracts_decision_reference() -> None:
    values = _values("Cass. civ. 1re, 12 janvier 2019.", EntityType.DECISION_REFERENCE)
    assert len(values) == 1


def test_extracts_person_with_title() -> None:
    assert "Maître Jean Dupont" in _values(
        "Représenté par Maître Jean Dupont.", EntityType.PERSON
    )


def test_extracts_company_with_legal_suffix() -> None:
    values = _values("La société ACME SARL est domiciliée à Paris.", EntityType.COMPANY)
    assert "ACME SARL" in values


def test_extracts_jurisdiction() -> None:
    assert "tribunal judiciaire" in _values(
        "Le tribunal judiciaire de Paris est compétent.", EntityType.JURISDICTION
    )


def test_extracts_address() -> None:
    values = _values("Domicilié au 12 rue de la Paix, 75002 Paris.", EntityType.ADDRESS)
    assert len(values) == 1
    assert "75002" in values[0]


def test_extracts_reference_to_exhibit() -> None:
    assert any("3" in v for v in _values("Voir pièce n°3 jointe au dossier.", EntityType.REFERENCE))


def test_extracts_generic_number() -> None:
    assert any("2024" in v for v in _values("Dossier n° 2024-0456.", EntityType.NUMBER))


def test_returns_empty_list_for_text_without_entities() -> None:
    assert RegexEntityExtractor().extract("Bonjour, comment allez-vous ?") == []


def test_entities_carry_span_information() -> None:
    entities = RegexEntityExtractor().extract("Voir article 1240 du code civil.")
    law_article = next(e for e in entities if e.type == EntityType.LAW_ARTICLE)
    assert law_article.span_start is not None
    assert law_article.span_end is not None
    assert law_article.span_end > law_article.span_start
