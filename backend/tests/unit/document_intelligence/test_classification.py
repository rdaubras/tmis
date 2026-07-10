from tmis.document_intelligence.classification.keyword_classifier import KeywordClassifier
from tmis.document_intelligence.schemas.classification import DocumentCategory


def test_classifies_contract() -> None:
    result = KeywordClassifier().classify(
        "Le présent contrat lie les parties, bailleur et locataire, avec clause de résiliation."
    )
    assert result.category == DocumentCategory.CONTRACT
    assert result.confidence > 0


def test_classifies_invoice() -> None:
    result = KeywordClassifier().classify(
        "Facture n°123, montant HT: 100, montant TTC: 120, échéance de paiement le 1er mars."
    )
    assert result.category == DocumentCategory.INVOICE


def test_classifies_case_law() -> None:
    result = KeywordClassifier().classify(
        "Arrêt de la Cour de cassation statuant sur le pourvoi formé par la Cour d'appel."
    )
    assert result.category == DocumentCategory.CASE_LAW


def test_defaults_to_other_when_no_keyword_matches() -> None:
    result = KeywordClassifier().classify("Un texte quelconque sans rapport juridique.")
    assert result.category == DocumentCategory.OTHER
    assert result.confidence == 0.0
    assert result.matched_keywords == ()


def test_confidence_reflects_keyword_coverage() -> None:
    partial = KeywordClassifier().classify("Ceci est un contrat.")
    fuller = KeywordClassifier().classify(
        "Ceci est un contrat entre les parties, avec bailleur, locataire, clause de résiliation."
    )
    assert fuller.confidence > partial.confidence
