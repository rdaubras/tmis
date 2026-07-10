import re

from tmis.legal_research.queries.schemas import ResearchQuery
from tmis.legal_research.queries.synonyms import expand

_TOKEN_RE = re.compile(r"[a-zà-ÿ]+", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")

_STOPWORDS: dict[str, frozenset[str]] = {
    "fr": frozenset(
        {
            "le", "la", "les", "de", "des", "du", "et", "en", "un", "une",
            "est", "que", "qui", "dans", "pour", "par", "avec", "au", "aux",
            "ce", "cette", "il", "elle", "sont", "sur", "quel", "quelle",
        }
    ),
    "en": frozenset(
        {
            "the", "of", "and", "a", "an", "is", "that", "which", "in",
            "for", "by", "with", "to", "it", "are", "this", "shall", "be",
        }
    ),
}


class HeuristicQueryEngine:
    """Implements `QueryEnginePort` with a dependency-free normalization,
    stopword-based language detection, keyword extraction, and a small
    legal synonym dictionary for query expansion (see
    docs/21-legal-research.md — Query Engine).

    Self-contained on purpose: the LRE stays independent of the Document
    Intelligence Engine even though both happen to solve language
    detection the same way.
    """

    def build(
        self, raw_text: str, filters: dict[str, object] | None = None
    ) -> ResearchQuery:
        normalized_text = _WHITESPACE_RE.sub(" ", raw_text.strip())
        tokens = [t.lower() for t in _TOKEN_RE.findall(normalized_text)]
        language = self._detect_language(tokens)
        stopwords = _STOPWORDS.get(language or "fr", frozenset())
        keywords = tuple(dict.fromkeys(t for t in tokens if t not in stopwords and len(t) > 2))
        expanded_terms = expand(keywords)
        return ResearchQuery(
            raw_text=raw_text,
            normalized_text=normalized_text,
            language=language,
            keywords=keywords,
            expanded_terms=expanded_terms,
            filters=dict(filters or {}),
        )

    def _detect_language(self, tokens: list[str]) -> str | None:
        if not tokens:
            return None
        scores = {lang: sum(1 for t in tokens if t in sw) for lang, sw in _STOPWORDS.items()}
        best_lang = max(scores, key=lambda lang: scores[lang])
        if scores[best_lang] == 0:
            return None
        return best_lang
