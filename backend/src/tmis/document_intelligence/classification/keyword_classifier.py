from tmis.document_intelligence.schemas.classification import (
    ClassificationResult,
    DocumentCategory,
)

_KEYWORDS: dict[DocumentCategory, tuple[str, ...]] = {
    DocumentCategory.CONTRACT: (
        "contrat", "les parties", "bailleur", "locataire", "clause", "résiliation",
    ),
    DocumentCategory.JUDGMENT: (
        "jugement", "le tribunal", "par ces motifs", "statuant publiquement",
    ),
    DocumentCategory.WRIT_OF_SUMMONS: (
        "assignation", "citation à comparaître", "sommation",
    ),
    DocumentCategory.PLEADINGS: (
        "conclusions", "plaise au tribunal", "demandeur", "défendeur",
    ),
    DocumentCategory.LETTER: (
        "madame, monsieur", "veuillez agréer", "courrier recommandé", "lettre recommandée",
    ),
    DocumentCategory.EXHIBIT: (
        "pièce n°", "pièce jointe", "annexe",
    ),
    DocumentCategory.INVOICE: (
        "facture", "montant ttc", "montant ht", "numéro de facture", "échéance de paiement",
    ),
    DocumentCategory.EMAIL: (
        "de :", "objet :", "envoyé le", "cc :", "pièces jointes :",
    ),
    DocumentCategory.CASE_LAW: (
        "cour de cassation", "cour d'appel", "arrêt", "pourvoi",
    ),
}

_DEFAULT_CATEGORY = DocumentCategory.OTHER


class KeywordClassifier:
    """Implements `ClassifierPort` with deterministic keyword matching.

    A learned classifier (e.g. a fine-tuned text model) is a natural
    future replacement behind the same port; this heuristic is enough to
    exercise the rest of the pipeline (knowledge graph, storage, export)
    end-to-end today (see docs/17-guide-nouveau-classifieur.md).
    """

    def classify(self, text: str) -> ClassificationResult:
        lowered = text.lower()
        best_category = _DEFAULT_CATEGORY
        best_matches: tuple[str, ...] = ()
        best_score = 0

        for category, keywords in _KEYWORDS.items():
            matches = tuple(kw for kw in keywords if kw in lowered)
            if len(matches) > best_score:
                best_score = len(matches)
                best_category = category
                best_matches = matches

        if best_score == 0:
            return ClassificationResult(category=_DEFAULT_CATEGORY, confidence=0.0)

        confidence = min(1.0, best_score / len(_KEYWORDS[best_category]))
        return ClassificationResult(
            category=best_category, confidence=confidence, matched_keywords=best_matches
        )
