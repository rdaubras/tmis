import re

from tmis.document_intelligence.schemas.entities import EntityType, ExtractedEntity

_MONTHS = (
    "janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre"
)

_DATE_PATTERNS = (
    re.compile(rf"\b\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}}\b", re.IGNORECASE),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
)
_AMOUNT_RE = re.compile(
    r"\b\d{1,3}(?:[ .]\d{3})*(?:,\d{2})?\s?(?:€|EUR|euros?)\b", re.IGNORECASE
)
_LAW_ARTICLE_RE = re.compile(r"\barticle\s+[A-Z]?\.?\s?\d[\w.-]*\b", re.IGNORECASE)
_DECISION_REFERENCE_RE = re.compile(
    rf"\bCass\.[^,;]{{0,60}},\s*\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}}\b", re.IGNORECASE
)
_PERSON_RE = re.compile(
    r"\b(?:M\.|Mme|Maître|Me)\s+[A-ZÀ-Ý][\wà-ÿÀ-Ý'-]+(?:\s+[A-ZÀ-Ý][\wà-ÿÀ-Ý'-]+)?"
)
_COMPANY_RE = re.compile(
    r"\b[A-Z][\w&'.-]*(?:\s+[A-Z][\w&'.-]*){0,4}\s+(?:SARL|SAS|SASU|SA|EURL|SCI)\b"
)
_JURISDICTION_KEYWORDS = (
    "tribunal judiciaire",
    "tribunal de commerce",
    "tribunal administratif",
    "cour d'appel",
    "cour de cassation",
    "conseil d'état",
    "conseil de prud'hommes",
)
_ADDRESS_RE = re.compile(
    r"\b\d{1,4}[, ]+(?:rue|avenue|boulevard|impasse|allée|place)\s+[\wà-ÿÀ-Ÿ'’ -]+?,?\s*"
    r"\d{5}\s+[A-ZÀ-Ÿ][\wà-ÿÀ-Ÿ'-]*",
    re.IGNORECASE,
)
_REFERENCE_RE = re.compile(r"\b(?:pièce|annexe)\s+n?°?\s?\d+\b", re.IGNORECASE)
_NUMBER_RE = re.compile(r"\bn°\s?\d[\d/-]*\b", re.IGNORECASE)

_HEURISTIC_CONFIDENCE = 0.6


class RegexEntityExtractor:
    """Implements `EntityExtractorPort` with dependency-free regular
    expressions tuned for French legal text.

    A trained NER model is a natural future replacement behind the same
    port; this heuristic already produces genuine, traceable spans, which
    is what the timeline and knowledge graph stages need (see
    docs/14-document-intelligence.md).
    """

    def extract(self, text: str) -> list[ExtractedEntity]:
        entities: list[ExtractedEntity] = []
        for pattern in _DATE_PATTERNS:
            entities += self._matches(pattern, text, EntityType.DATE)
        entities += self._matches(_AMOUNT_RE, text, EntityType.AMOUNT)
        entities += self._matches(_DECISION_REFERENCE_RE, text, EntityType.DECISION_REFERENCE)
        entities += self._matches(_LAW_ARTICLE_RE, text, EntityType.LAW_ARTICLE)
        entities += self._matches(_PERSON_RE, text, EntityType.PERSON)
        entities += self._matches(_COMPANY_RE, text, EntityType.COMPANY)
        entities += self._matches(_ADDRESS_RE, text, EntityType.ADDRESS)
        entities += self._matches(_REFERENCE_RE, text, EntityType.REFERENCE)
        entities += self._matches(_NUMBER_RE, text, EntityType.NUMBER)
        entities += self._keyword_matches(text, _JURISDICTION_KEYWORDS, EntityType.JURISDICTION)
        return entities

    def _matches(
        self, pattern: re.Pattern[str], text: str, entity_type: EntityType
    ) -> list[ExtractedEntity]:
        return [
            ExtractedEntity(
                type=entity_type,
                value=match.group(0),
                confidence=_HEURISTIC_CONFIDENCE,
                span_start=match.start(),
                span_end=match.end(),
            )
            for match in pattern.finditer(text)
        ]

    def _keyword_matches(
        self, text: str, keywords: tuple[str, ...], entity_type: EntityType
    ) -> list[ExtractedEntity]:
        lowered = text.lower()
        results = []
        for keyword in keywords:
            start = 0
            while (index := lowered.find(keyword, start)) != -1:
                results.append(
                    ExtractedEntity(
                        type=entity_type,
                        value=text[index : index + len(keyword)],
                        confidence=_HEURISTIC_CONFIDENCE,
                        span_start=index,
                        span_end=index + len(keyword),
                    )
                )
                start = index + len(keyword)
        return results
