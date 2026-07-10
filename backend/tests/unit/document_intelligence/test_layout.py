from tmis.document_intelligence.layout.heuristic_analyzer import HeuristicLayoutAnalyzer
from tmis.document_intelligence.schemas.layout import BlockType


def _types(text: str) -> list[BlockType]:
    return [block.type for block in HeuristicLayoutAnalyzer().analyze(text)]


def test_detects_uppercase_title() -> None:
    assert BlockType.TITLE in _types("CONTRAT DE BAIL COMMERCIAL\n\nCeci est un paragraphe normal.")


def test_detects_subtitle() -> None:
    assert BlockType.SUBTITLE in _types("1.1 Modalités de paiement\nLe loyer est payable.")


def test_detects_list_items() -> None:
    types = _types("- Premier point\n- Deuxième point")
    assert types == [BlockType.LIST, BlockType.LIST]


def test_detects_signature_line() -> None:
    assert BlockType.SIGNATURE in _types("Fait à Paris, le 10 janvier 2024")


def test_detects_annex() -> None:
    assert BlockType.ANNEX in _types("Annexe 1 : Inventaire du mobilier")


def test_detects_footnote() -> None:
    assert BlockType.FOOTNOTE in _types("(1) Voir la clause 3 ci-dessus.")


def test_detects_table_like_line() -> None:
    assert BlockType.TABLE in _types("Nom\tMontant\tDate")


def test_default_block_type_is_paragraph() -> None:
    types = _types("Ceci est une phrase normale qui ne correspond à aucun motif particulier.")
    assert types == [BlockType.PARAGRAPH]


def test_detects_repeated_header_and_footer_across_pages() -> None:
    page = "CABINET JURIDIQUE\nContenu de la page.\nPage confidentielle"
    text = "\x0c".join([page, page])
    types = _types(text)
    assert BlockType.HEADER in types
    assert BlockType.FOOTER in types


def test_preserves_reading_order() -> None:
    blocks = HeuristicLayoutAnalyzer().analyze("Premier\nDeuxième\nTroisième")
    assert [b.order for b in blocks] == [0, 1, 2]
