from tmis.document_intelligence.chunking.fixed_size_strategy import FixedSizeChunkingStrategy
from tmis.document_intelligence.chunking.structural_chunker import StructuralChunker
from tmis.document_intelligence.layout.heuristic_analyzer import HeuristicLayoutAnalyzer

_TEXT = (
    "CONTRAT DE BAIL COMMERCIAL\n\n"
    "Le présent contrat est conclu entre les parties.\n\n"
    "1.1 Modalités de paiement\n\n"
    "Le loyer mensuel est de 1500 EUR, payable le 5 de chaque mois."
)


def test_structural_chunker_starts_a_new_chunk_at_each_title() -> None:
    blocks = HeuristicLayoutAnalyzer().analyze(_TEXT)
    chunks = StructuralChunker().chunk("doc-1", _TEXT, blocks)

    assert len(chunks) == 2
    assert chunks[0].metadata["section"] == "CONTRAT DE BAIL COMMERCIAL"
    assert chunks[1].metadata["section"] == "1.1 Modalités de paiement"


def test_structural_chunker_keeps_title_text_inside_its_chunk() -> None:
    blocks = HeuristicLayoutAnalyzer().analyze(_TEXT)
    chunks = StructuralChunker().chunk("doc-1", _TEXT, blocks)

    assert "CONTRAT DE BAIL COMMERCIAL" in chunks[0].content


def test_structural_chunker_respects_max_chunk_size_within_a_section() -> None:
    long_paragraph = "Paragraphe très long. " * 100
    text = f"TITRE\n\n{long_paragraph}"
    blocks = HeuristicLayoutAnalyzer().analyze(text)

    chunks = StructuralChunker(max_chunk_chars=500).chunk("doc-1", text, blocks)

    assert len(chunks) > 1
    assert all(chunk.document_id == "doc-1" for chunk in chunks)


def test_structural_chunker_skips_headers_and_footers() -> None:
    page = "EN-TETE\nContenu utile de la page.\nPIED DE PAGE"
    text = "\x0c".join([page, page])
    blocks = HeuristicLayoutAnalyzer().analyze(text)

    chunks = StructuralChunker().chunk("doc-1", text, blocks)

    joined = "\n".join(chunk.content for chunk in chunks)
    assert "EN-TETE" not in joined
    assert "PIED DE PAGE" not in joined


def test_fixed_size_strategy_ignores_layout_and_splits_by_size() -> None:
    text = "x" * 1000
    blocks = HeuristicLayoutAnalyzer().analyze(text)

    chunks = FixedSizeChunkingStrategy(chunk_size=400, overlap=50).chunk("doc-1", text, blocks)

    assert len(chunks) > 1
    assert len(chunks[0].content) == 400
