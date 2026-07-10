import re

_TOKEN_RE = re.compile(r"[a-zà-ÿ]+", re.IGNORECASE)

_STOPWORDS: dict[str, frozenset[str]] = {
    "fr": frozenset(
        {
            "le", "la", "les", "de", "des", "du", "et", "en", "un", "une",
            "est", "que", "qui", "dans", "pour", "par", "avec", "au", "aux",
            "ce", "cette", "il", "elle", "sont", "articles", "article",
        }
    ),
    "en": frozenset(
        {
            "the", "of", "and", "a", "an", "is", "that", "which", "in",
            "for", "by", "with", "to", "it", "are", "this", "shall", "be",
        }
    ),
}


class HeuristicLanguageDetector:
    """Implements `LanguageDetectorPort` with a dependency-free stopword
    frequency comparison between French and English.

    Sprint 3 scope: enough to distinguish the two languages TMIS
    currently targets; a statistical/ML detector can be swapped in later
    behind the same port without touching the pipeline.
    """

    def detect(self, text: str) -> str | None:
        tokens = [t.lower() for t in _TOKEN_RE.findall(text)]
        if not tokens:
            return None
        scores = {
            lang: sum(1 for t in tokens if t in stopwords)
            for lang, stopwords in _STOPWORDS.items()
        }
        best_lang = max(scores, key=lambda lang: scores[lang])
        if scores[best_lang] == 0:
            return None
        return best_lang
