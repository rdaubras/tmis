import re

from tmis.ai_fabric.evaluation.schemas import ResponseMetrics

_CITATION_PATTERN = re.compile(
    r"(art\.|article\s+\d+|cass\.|cour\s+de|jurisprudence|\[\d+\])", re.IGNORECASE
)
_NEGATION_MARKERS = ("ne pas", "n'est pas", "jamais", "aucun", "aucune", "ne peut pas")
_SIMILARITY_THRESHOLD_FOR_CONTRADICTION = 0.5


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _words(text: str) -> frozenset[str]:
    return frozenset(re.findall(r"\w+", text.lower()))


def jaccard_similarity(a: str, b: str) -> float:
    """Word-set overlap — a small, dependency-free heuristic (no
    embedding call) reused by `comparison/`, `consensus/`, and
    `fusion/` to gauge how much two texts overlap."""
    words_a, words_b = _words(a), _words(b)
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def _find_contradictions(sentences: list[str]) -> tuple[str, ...]:
    flags: list[str] = []
    for i, sentence_a in enumerate(sentences):
        negated_a = any(marker in sentence_a.lower() for marker in _NEGATION_MARKERS)
        for sentence_b in sentences[i + 1 :]:
            negated_b = any(marker in sentence_b.lower() for marker in _NEGATION_MARKERS)
            if negated_a != negated_b and (
                jaccard_similarity(sentence_a, sentence_b)
                > _SIMILARITY_THRESHOLD_FOR_CONTRADICTION
            ):
                flags.append(f"contradiction potentielle : {sentence_a!r} vs {sentence_b!r}")
    return tuple(flags)


class ResponseEvaluator:
    """Computes `ResponseMetrics` for a raw model response. Never
    calls a model itself — every score is a deterministic heuristic,
    so evaluation is cheap, reproducible, and explainable."""

    def evaluate(self, text: str) -> ResponseMetrics:
        sentences = _sentences(text)
        contradictions = _find_contradictions(sentences)
        coherence_score = 1.0 - min(1.0, len(contradictions) / max(1, len(sentences)))
        return ResponseMetrics(
            length_words=len(text.split()),
            citation_count=len(_CITATION_PATTERN.findall(text)),
            coherence_score=coherence_score,
            contradiction_flags=contradictions,
        )
